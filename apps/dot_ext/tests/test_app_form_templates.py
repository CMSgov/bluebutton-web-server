import uuid

# from random import randrange
import pytest
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.db.models.fields import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    EmailField,
    TextField,
    URLField,
)
from django.template.base import VariableNode
from django.template.loader import get_template
from waffle.testutils import override_switch

from apps.dot_ext.forms import CustomRegisterApplicationForm
from apps.dot_ext.models import Application

# from apps.test import BaseApiTest


def get_form_fields(frm):
    """
    helper: extract all fields names from a form
    """
    fields = list(frm.base_fields)
    for field in list(frm.declared_fields):
        if field not in fields:
            fields.append(field)
    return fields


def extract_flds_from_html(html_doc):
    """Returns all form tags found on a web page's `url`"""
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup.find_all('input')


def generate_app(app):
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


def get_page(tmplt, ctx):
    temp = get_template(tmplt)
    return temp.render({'application': ctx})


def get_ref_flds_from_template(tmplt, ctx_prefix):
    temp = get_template(tmplt)
    nodes = temp.template.nodelist.get_nodes_by_type(VariableNode)
    prefix_len = len(ctx_prefix)
    ref_fields = [n.token.contents[prefix_len + 1 :] for n in nodes]
    return ref_fields


def check_template(frm, tmplt, ctx_prefix, switch_active):
    """
    helper: validate form <frm> against its template <tmplt> for dangling vars
    """
    form_fields = get_form_fields(frm)
    ref_fields = get_ref_flds_from_template(tmplt, ctx_prefix)
    # If the switch is disabled, we expect jwks_uri to NOT be in the active reference fields
    if not switch_active:
        ref_fields = [f for f in ref_fields if f != 'jwks_uri']
    diff_flds = set(ref_fields) - set(form_fields)
    assert set(ref_fields).issubset(set(form_fields)), (
        'template {} referenced fields {} not in application context.'.format(tmplt, diff_flds)
    )
    context = {
        ctx_prefix: {f: uuid.uuid4().hex for f in ref_fields},
    }

    temp = get_template(tmplt)
    page_w_fld = temp.render(context)

    if not switch_active:
        assert 'jwks_uri' not in page_w_fld, 'jwks_uri was found in HTML even though the switch is disabled.'

    # assert rendering values
    ctx = context[ctx_prefix]
    for k in ref_fields:
        assert ctx[k] in page_w_fld, 'Var [{}] value [{}] not found in rendered page.'.format(k, ctx[k])


@pytest.mark.django_db
@pytest.mark.parametrize('switch_active', [True, False])
def test_app_forms_templates(switch_active, basic_user):
    """
    Check vars in template html are consistent with corresponding context (model)
    Runs twice: once with the switch active (True) and once inactive (False).
    """
    u = basic_user()
    form = CustomRegisterApplicationForm(u)

    with override_switch('asymmetric_auth_validation', active=switch_active):
        check_template(form, 'include/app-form-required-info.html', 'application', switch_active)
        check_template(form, 'include/app-form-optional-info.html', 'application', switch_active)


def test_app_form_template_with_default_initvalues(basic_user, create_application):
    """
    Test use cases where optional form fields can be saved with their default init values
    """
    template_doc = 'include/app-form-optional-info.html'
    u = basic_user()
    app = create_application(
        'template_test_app',
        Application.CLIENT_CONFIDENTIAL,
        Application.GRANT_AUTHORIZATION_CODE,
        user=u,
        agree=True,
        redirect_uris='http://localhost:3000/test_redirect_url',
    )
    app_fields = generate_app(app)
    page_opt = get_page(template_doc, app_fields)
    ref_fields = get_ref_flds_from_template(template_doc, 'application')
    opt_flds_rendered = extract_flds_from_html(page_opt)
    for input in opt_flds_rendered:
        input_name = input['name']
        if input_name in ref_fields:
            app_fields[input_name] = input.get('value')
    app_fields['name'] = 'template_test_app_valid'
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
    assert passed, 'ValidationError not expected.'
