import uuid
from django.test import TestCase
from django.template import loader
from django.template.base import VariableNode
from apps.dot_ext.admin import CustomAdminApplicationForm


def get_form_fields(frm):
    '''
    helper: extract all fields names from a form
    '''
    fields = list(frm().base_fields)
    for field in list(frm().declared_fields):
        if field not in fields:
            fields.append(field)
    return fields


class AppFormTemplateTestCase(TestCase):
    """
    Test Application Form templates
    Check: no dangling var reference in template html, vars are properly rendered with values
    """
    def check_template(self, frm, tmplt, ctx_prefix):
        '''
        helper: validate form <frm> against its template <tmplt> for dangling vars
        '''
        form_fields = get_form_fields(frm)
        temp = loader.get_template(tmplt)
        nodes = temp.template.nodelist.get_nodes_by_type(VariableNode)
        prefix_len = len(ctx_prefix)
        ref_fields = [n.token.contents[prefix_len + 1:] for n in nodes]
        diff_flds = set(ref_fields) - set(form_fields)
        self.assertTrue(set(ref_fields).issubset(set(form_fields)),
                        "template {} referenced fields {} not in application context.".format(tmplt, diff_flds))
        context = {
            ctx_prefix: {f: uuid.uuid4().hex for f in ref_fields},
        }
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
        self.check_template(CustomAdminApplicationForm, 'include/app-form-required-info.html', 'application')
        self.check_template(CustomAdminApplicationForm, 'include/app-form-optional-info.html', 'application')
