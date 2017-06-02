import logging
from random import randint

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext_lazy as _

from .models import Invitation, RequestInvite, UserProfile, create_activation_key, UserRegisterCode
from .models import QUESTION_1_CHOICES, QUESTION_2_CHOICES, QUESTION_3_CHOICES, MFA_CHOICES
from localflavor.us.forms import USPhoneNumberField
import csv

logger = logging.getLogger('hhs_server.%s' % __name__)


class BulkUserCodeForm(forms.Form):
    csv_text = forms.CharField(widget=forms.Textarea, max_length=10240, label=_(
        'CSV including header row'), help_text=_('id,first_name,last_name,email,username,code'))
    required_css_class = 'required'

    def clean_csv_text(self):
        csv_text = self.cleaned_data.get('csv_text', '')
        dreader = csv.DictReader(str.splitlines(str(csv_text)))
        headers = dreader.fieldnames
        for row in dreader:
            if len(row) != 6:
                raise forms.ValidationError(_('Each row must have 6 values'))
        header = ['id', 'first_name', 'last_name', 'email', 'username', 'code']
        (header > headers) - (header < headers)
        if (header > headers) - (header < headers) != 0:
            raise forms.ValidationError(
                _('check the values or your header row'))
        return csv_text


class RequestInviteForm(forms.ModelForm):

    class Meta:
        model = RequestInvite
        fields = ('first_name', 'last_name', 'email', 'user_type')

    user_type = 'DEV'
    human_x = randint(1, 9)
    human_y = randint(1, 9)
    human_z = human_x + human_y
    human_q = ('What is %s + %s?' % (human_x, human_y))
    human = forms.CharField(
        max_length=30,
        label=_(human_q),
        help_text='We are asking this to make sure you are human. '
                  'Hint: the answer is %s.' % human_z,
    )
    required_css_class = 'required'

    def clean_human(self):
        human = self.cleaned_data.get('human', '')
        logger.debug("Compare [%s] to [%s]" % (str(human), str(self.human_z)))
        if str(human) != str(self.human_z):
            raise forms.ValidationError(_('You are either not human or '
                                          'just just really bad at math.'))
        return human


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
    email = forms.CharField(max_length=75, label=_('Email or User Name'))
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
    username = forms.CharField(max_length=30, label=_('User'))
    password = forms.CharField(widget=forms.PasswordInput, max_length=120,
                               label=_('Password'))
    required_css_class = 'required'

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.rstrip().lstrip().lower()


class CodeLoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_('Username'),
                               help_text="MyMedicare.gov user name")
    password = forms.CharField(widget=forms.PasswordInput, max_length=120,
                               label=_('Password'),
                               help_text="MyMedicare.gov password")
    code = forms.CharField(
        max_length=30,
        label=_('Code'),
        help_text="The code provided by your accountable care organization")
    required_css_class = 'required'

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.rstrip().lstrip().lower()


class EndUserRegisterForm(forms.Form):
    code = forms.CharField(
        max_length=30,
        label=_('Code'),
        help_text="The code provided by your accountable care organization")
    username = forms.CharField(max_length=30, label=_('Username'),
                               help_text="Your desired user name")
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_('Password'),
                                help_text="Set your password")

    password2 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_('Password (again)'),
                                help_text="Set your Password")

    password_reset_question_1 = forms.ChoiceField(choices=QUESTION_1_CHOICES)
    password_reset_answer_1 = forms.CharField(max_length=50)
    password_reset_question_2 = forms.ChoiceField(choices=QUESTION_2_CHOICES)
    password_reset_answer_2 = forms.CharField(max_length=50)
    password_reset_question_3 = forms.ChoiceField(choices=QUESTION_3_CHOICES)
    password_reset_answer_3 = forms.CharField(max_length=50)
    mobile_phone_number = USPhoneNumberField(required=False,
                                             label=_("Mobile Phone Number "
                                                     "(Optional)"),
                                             help_text=_("We use this for "
                                                         "multi-factor "
                                                         "authentication. "
                                                         "US numbers only."))
    code = forms.CharField(
        max_length=30,
        label=_('Code'),
        help_text="The code provided to you.")
    required_css_class = 'required'

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not UserRegisterCode.objects.filter(code=code, used=False).exists():
            raise forms.ValidationError(_('The code provided is invalid.'))
        return code

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.rstrip().lstrip().lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')
        if password1 != password2:
            raise forms.ValidationError(_('The two password fields '
                                          'didn\'t match.'))

        try:
            validate_password(password1)
        except ValidationError as err:
            raise forms.ValidationError(err.error_list[0])
        return password2

    def save(self):

        code = self.cleaned_data.get('code', '')
        # Get the invitation.
        urc = UserRegisterCode.objects.get(code=code, used=False)

        new_user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=urc.first_name,
            last_name=urc.last_name,
            password=self.cleaned_data['password1'],
            email=urc.email,
            is_active=False)

        UserProfile.objects.create(user=new_user,
                                   user_type="BEN",
                                   create_applications=False,
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
        group = Group.objects.get(name='BlueButton')
        new_user.groups.add(group)

        # Add the user id to the crosswalk...
        from ..fhir.bluebutton.models import Crosswalk
        Crosswalk.objects.create(user=new_user, user_id_hash=urc.user_id_hash)

        # Send a verification email
        create_activation_key(new_user)
        urc.delete()
        return new_user


class SignupForm(forms.Form):
    invitation_code = forms.CharField(max_length=30, label=_("Invitation Code")
                                      )
    username = forms.CharField(max_length=30, label=_("User"))
    email = forms.EmailField(max_length=75, label=_("Email"))
    first_name = forms.CharField(max_length=100, label=_("First Name"))
    last_name = forms.CharField(max_length=100, label=_("Last Name"))
    mobile_phone_number = USPhoneNumberField(required=False,
                                             label=_("Mobile Phone Number "
                                                     "(Optional)"),
                                             help_text=_("We use this for "
                                                         "multi-factor "
                                                         "authentication. "
                                                         "US numbers only."))
    organization_name = forms.CharField(max_length=100,
                                        label=_("Organization Name"),
                                        required=False
                                        )
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_("Password (again)"))
    password_reset_question_1 = forms.ChoiceField(choices=QUESTION_1_CHOICES)
    password_reset_answer_1 = forms.CharField(max_length=50)
    password_reset_question_2 = forms.ChoiceField(choices=QUESTION_2_CHOICES)
    password_reset_answer_2 = forms.CharField(max_length=50)
    password_reset_question_3 = forms.ChoiceField(choices=QUESTION_3_CHOICES)
    password_reset_answer_3 = forms.CharField(max_length=50)

    required_css_class = 'required'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data.get("password2", "")
        if password1 != password2:
            raise forms.ValidationError(
                _("The two password fields didn't match."))

        try:
            validate_password(password1)
        except ValidationError as err:
            raise forms.ValidationError(err.error_list[0])

        return password2

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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username = username.rstrip().lstrip().lower()

        if User.objects.filter(username=username).count() > 0:
            raise forms.ValidationError(_('This username is already taken.'))
        return username

    def clean_invitation_code(self):
        invitation_code = self.cleaned_data['invitation_code']
        if Invitation.objects.filter(valid=True,
                                     code=invitation_code).count() != 1:
            raise forms.ValidationError(_('The invitation code is not valid.'))
        return invitation_code

    def save(self):

        invitation_code = self.cleaned_data['invitation_code']
        # make the invitation a invalid/spent.
        invite = Invitation.objects.get(code=str(invitation_code), valid=True)
        invite.valid = False
        invite.save()

        new_user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'],
            is_active=False)

        UserProfile.objects.create(user=new_user,
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
        group = Group.objects.get(name='BlueButton')
        new_user.groups.add(group)

        # Send a verification email
        create_activation_key(new_user)

        return new_user


class AccountSettingsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AccountSettingsForm, self).__init__(*args, **kwargs)

    username = forms.CharField(max_length=30, label=_('User Name'))
    email = forms.CharField(max_length=30, label=_('Email'))
    first_name = forms.CharField(max_length=100, label=_('First Name'))
    last_name = forms.CharField(max_length=100, label=_('Last Name'))
    mfa_login_mode = forms.ChoiceField(required=False,
                                       choices=MFA_CHOICES,
                                       help_text=_("Change this to turn on "
                                                   "multi-factor "
                                                   "authentication (MFA)."))
    mobile_phone_number = USPhoneNumberField(required=False,
                                             help_text=_("US numbers only. "
                                                         "We use this for "
                                                         "multi-factor "
                                                         "authentication."))
    organization_name = forms.CharField(max_length=100,
                                        label=_('Organization Name'),
                                        required=False)
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

    def clean_mobile_phone_number(self):
        mobile_phone_number = self.cleaned_data.get('mobile_phone_number', '')
        mfa_login_mode = self.cleaned_data.get('mfa_login_mode', '')
        if mfa_login_mode == "SMS" and not mobile_phone_number:
            raise forms.ValidationError(
                _('A mobile phone number is required to use SMS-based '
                  'multi-factor authentication'))
        return mobile_phone_number

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username = username.rstrip().lstrip().lower()
        if username and User.objects.filter(
                username=username).exclude(username=username).count():
            raise forms.ValidationError(_('This username is already taken.'))
        return username
