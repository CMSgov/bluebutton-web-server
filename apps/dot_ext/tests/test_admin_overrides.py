import pytest

from apps.dot_ext.admin_overrides import ValidatedApplicationAdminForm


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    [
        '<img src=x onerror=alert(document.domain)>',
        '<img src=x onerror=alert(document.domain)',
        '<svg/onload=alert(document.domain)>',
        '<script>alert(document.domain)</script>',
        'Acme SDK <Beta>',
    ],
)
def test_application_admin_rejects_html_names(name):
    form = ValidatedApplicationAdminForm(data={'name': name})

    assert not form.is_valid()
    assert form.errors['name'] == [
        'Application names cannot contain angle brackets (< or >). Please use plain-text only!'
    ]


@pytest.mark.django_db
def test_application_admin_preserves_plain_text_punctuation():
    form = ValidatedApplicationAdminForm(data={'name': 'Research & Analytics (v2): A = B'})

    form.is_valid()

    assert 'name' not in form.errors
