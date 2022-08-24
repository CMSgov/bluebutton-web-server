import uuid
from random import randrange
from django.template.loader import get_template
from django.template.base import VariableNode
from apps.dot_ext.forms import CustomRegisterApplicationForm
from apps.dot_ext.models import Application
from django.core.exceptions import ValidationError

from apps.test import BaseApiTest
from bs4 import BeautifulSoup
from django.db.models.fields import (
    CharField,
    URLField,
    DateTimeField,
    TextField,
    BooleanField,
    BigIntegerField,
    EmailField,
)


def get_form_fields(frm):
    '''
    helper: extract all fields names from a form
    '''
    fields = list(frm.base_fields)
    for field in list(frm.declared_fields):
        if field not in fields:
            fields.append(field)
    return fields


def extract_flds_from_html(html_doc):
    """Returns all form tags found on a web page's `url` """
    soup = BeautifulSoup(html_doc, "html.parser")
    return soup.find_all("input")


class AppFormTemplateTestCase(BaseApiTest):
    """
    Test Application Form templates
    Check: no dangling var reference in template html, vars are properly rendered with values
    """
    def get_page(self, tmplt, ctx):
        temp = get_template(tmplt)
        return temp.render({'application': ctx})

    def create_user(self):
        rn = randrange(100)
        template_group = self._create_group('template_render_{}'.format(rn))
        self._create_capability('Template-Render-Scope-{}'.format(rn), [], template_group)
        user = self._create_user('template_tester_{}'.format(rn), 'bluebutton_{}'.format(rn))
        user.groups.add(template_group)
        return user

    def generate_app(self, app):
        app_flds = {}
        app_fields_meta = app._meta.get_fields()
        for fm in app_fields_meta:
            if isinstance(fm, (CharField, URLField, DateTimeField, TextField, BooleanField, BigIntegerField, EmailField)):
                fld_name = fm.name
                fld_val = fm.value_from_object(app)
                if fld_val is None and fm.null:
                    # if nullable set init value to None
                    app_flds[fld_name] = None
                app_flds[fld_name] = fld_val
        return app_flds

    def get_ref_flds_from_template(self, tmplt, ctx_prefix):
        temp = get_template(tmplt)
        nodes = temp.template.nodelist.get_nodes_by_type(VariableNode)
        prefix_len = len(ctx_prefix)
        ref_fields = [n.token.contents[prefix_len + 1:] for n in nodes]
        return ref_fields

    def check_template(self, frm, tmplt, ctx_prefix):
        '''
        helper: validate form <frm> against its template <tmplt> for dangling vars
        '''
        form_fields = get_form_fields(frm)
        ref_fields = self.get_ref_flds_from_template(tmplt, ctx_prefix)
        diff_flds = set(ref_fields) - set(form_fields)
        self.assertTrue(set(ref_fields).issubset(set(form_fields)),
                        "template {} referenced fields {} not in application context.".format(tmplt, diff_flds))
        context = {
            ctx_prefix: {f: uuid.uuid4().hex for f in ref_fields},
        }

        temp = get_template(tmplt)
        page_w_fld = temp.render(context)
        # assert rendering values
        ctx = context[ctx_prefix]
        for k in ref_fields:
            self.assertIn(ctx[k], page_w_fld, "Var [{}] value [{}] not found in rendered page.".format(k, ctx[k]))

    def test_app_forms_templates(self):
        """
        Check vars in template html is consistent
        with corresponding context (model)
        """
        u = self.create_user()
        form = CustomRegisterApplicationForm(u)
        self.check_template(form, 'include/app-form-required-info.html', 'application')
        self.check_template(form, 'include/app-form-optional-info.html', 'application')

    def test_app_form_template_with_default_initvalues(self):
        """
        Test use cases where optional form fields can be saved with their default init values
        """
        template_doc = 'include/app-form-optional-info.html'
        u = self.create_user()
        app = self._create_application('template_test_app',
                                       Application.CLIENT_CONFIDENTIAL,
                                       Application.GRANT_AUTHORIZATION_CODE,
                                       user=u,
                                       agree=True,
                                       redirect_uris='http://localhost:3000/test_redirect_url')
        app_fields = self.generate_app(app)
        page_opt = self.get_page(template_doc, app_fields)
        ref_fields = self.get_ref_flds_from_template(template_doc, 'application')
        opt_flds_rendered = extract_flds_from_html(page_opt)
        for input in opt_flds_rendered:
            input_name = input['name']
            if input_name in ref_fields:
                app_fields[input_name] = input.get('value')
        app_fields['name'] = "template_test_app_valid"
        # save with values scrapped from rendered page
        # pass if no validation error
        form = CustomRegisterApplicationForm(u, app_fields)
        app_model = form.instance
        app_model.user = u
        passed = True
        try:
            form.save()
        except ValidationError:
            passed = False
        self.assertTrue(passed, 'ValidationError not expected.')
