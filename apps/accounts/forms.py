import logging
from django.conf import settings
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext_lazy as _
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter
from .models import UserProfile, create_activation_key
from .models import QUESTION_1_CHOICES, QUESTION_2_CHOICES, QUESTION_3_CHOICES, MFA_CHOICES
from django.contrib.auth.forms import AuthenticationForm, UsernameField


logger = logging.getLogger('hhs_server.%s' % __name__)


class SecretQuestionForm(forms.Form):
    answer = forms.CharField(max_length=50)
    required_css_class = 'required'


class ChangeSecretQuestionsForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('password_reset_question_1',
                  'password_reset_answer_1',
                  'password_reset_question_2',
                  'password_reset_answer_2',
                  'password_reset_question_3',
                  'password_reset_answer_3')

    def __init__(self, *args, **kwargs):
        super(ChangeSecretQuestionsForm, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = True


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(max_length=255, label=_('Email'))

    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        return email.rstrip().lstrip().lower()
    required_css_class = 'required'


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_('Password*'))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_('Password (again)*'))

    required_css_class = 'required'

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data['password2']
        if password1 != password2:
            raise forms.ValidationError(_('The two password fields '
                                          'didn\'t match.'))

        try:
            validate_password(password1)
        except ValidationError as err:
            raise forms.ValidationError(err.error_list[0])
        return password2


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_('Username'))
    password = forms.CharField(widget=forms.PasswordInput, max_length=120,
                               label=_('Password'))
    required_css_class = 'required'

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.rstrip().lstrip().lower()


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=255,
                             label=_("Email"),
                             help_text=_("Your email address is needed for "
                                         "password reset and other "
                                         "notifications."))
    first_name = forms.CharField(max_length=100,
                                 label=_("First Name"))
    last_name = forms.CharField(max_length=100,
                                label=_("Last Name"))
    organization_name = forms.CharField(max_length=100,
                                        label=_("Organization Name"),
                                        required=True
                                        )
    password1 = forms.CharField(widget=forms.PasswordInput,
                                max_length=120,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput,
                                max_length=120,
                                label=_("Password (again)"),
                                help_text=_("We are asking you to re-enter "
                                            "your chosen password to make "
                                            "sure it was entered correctly."))
    password_reset_question_1 = forms.ChoiceField(choices=QUESTION_1_CHOICES)
    password_reset_answer_1 = forms.CharField(max_length=50)
    password_reset_question_2 = forms.ChoiceField(choices=QUESTION_2_CHOICES)
    password_reset_answer_2 = forms.CharField(max_length=50)
    password_reset_question_3 = forms.ChoiceField(choices=QUESTION_3_CHOICES)
    password_reset_answer_3 = forms.CharField(max_length=50,
                                              help_text=_("We use your "
                                                          "answers during any "
                                                          "password reset "
                                                          "request. <br/>"
                                                          "Make sure you "
                                                          "remember your "
                                                          "answers!"))

    required_css_class = 'required'

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'organization_name', 'password1', 'password2',
                  'password_reset_question_1', 'password_reset_answer_1', 'password_reset_question_2',
                  'password_reset_answer_2', 'password_reset_question_3', 'password_reset_answer_3',
                  )

    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        if email:
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(
                    username=username).count():
                raise forms.ValidationError(
                    _('This email address is already registered.'))
            return email.rstrip().lstrip().lower()
        else:
            return email.rstrip().lstrip().lower()

    def save(self):
        self.instance.username = self.instance.email
        self.instance.is_active = False
        user = super().save()

        UserProfile.objects.create(user=user,
                                   organization_name=self.cleaned_data[
                                       'organization_name'],
                                   user_type="DEV",
                                   create_applications=True,
                                   password_reset_question_1=self.cleaned_data[
                                       'password_reset_question_1'],
                                   password_reset_answer_1=self.cleaned_data[
                                       'password_reset_answer_1'],
                                   password_reset_question_2=self.cleaned_data[
                                       'password_reset_question_2'],
                                   password_reset_answer_2=self.cleaned_data[
                                       'password_reset_answer_2'],
                                   password_reset_question_3=self.cleaned_data[
                                       'password_reset_question_3'],
                                   password_reset_answer_3=self.cleaned_data[
                                       'password_reset_answer_3']
                                   )
        # Attach the user to the default patient.
        Crosswalk.objects.create(user=user, fhir_source=get_resourcerouter(),
                                 fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID)

        group = Group.objects.get(name='BlueButton')
        user.groups.add(group)

        # Send a verification email
        create_activation_key(user)

        return user


class AccountSettingsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AccountSettingsForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(max_length=255, label=_('Email'))
    first_name = forms.CharField(max_length=100, label=_('First Name'))
    last_name = forms.CharField(max_length=100, label=_('Last Name'))
    mfa_login_mode = forms.ChoiceField(required=False,
                                       choices=MFA_CHOICES,
                                       help_text=_("Change this to turn on "
                                                   "multi-factor "
                                                   "authentication (MFA)."))
    organization_name = forms.CharField(max_length=100,
                                        label=_('Organization Name'),
                                        required=True)
    create_applications = forms.BooleanField(initial=False,
                                             required=False)
    required_css_class = 'required'

    def clean_mfa_login_mode(self):
        mfa_login_mode = self.cleaned_data.get('mfa_login_mode')
        if self.request.user.is_staff and not mfa_login_mode:
            raise forms.ValidationError(_('MFA is not optional for staff.'))
        return mfa_login_mode

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if email and User.objects.filter(
                    email=email).exclude(email=email).count():
                raise forms.ValidationError(_('This email address is '
                                              'already registered.'))
        return email.rstrip().lstrip().lower()


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True}),
                             max_length=150, label=_('Email'))
    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password."
        ),
        'inactive': _("This account is inactive."),
    }

    required_css_class = 'required'

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.rstrip().lstrip().lower()
