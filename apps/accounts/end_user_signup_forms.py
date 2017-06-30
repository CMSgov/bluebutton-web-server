import logging
from random import randint

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext_lazy as _

from .models import UserProfile, create_activation_key, UserRegisterCode
from localflavor.us.forms import USPhoneNumberField
from django.utils.dates import MONTHS
from .views.core import MFA_CHOICES
logger = logging.getLogger('hhs_server.%s' % __name__)

MEDICARE_SUFFIX_CHOICES = (('A', 'A'), ('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'),
                           ('A4', 'A4'), ('A5', 'A5'), ('A6',
                                                        'A6'), ('A7', 'A7'), ('A8', 'A8'),
                           ('A9', 'A9'), ('B', 'B'), ('B1',
                                                      'B1'), ('B2', 'B2'), ('B3', 'B3'),
                           ('B4', 'B4'), ('B5', 'B5'), ('B6', 'B6'), ('B7', 'B7'))


class SimpleUserSignupForm(forms.Form):
    invitation_code = forms.CharField(max_length=30, label=_("Invitation Code *"),
                                      help_text=_("While in pilot mode, "
                                                  "an invitation code "
                                                  "is needed to register.")
                                      )
    first_name = forms.CharField(max_length=100, label=_("First Name"))
    last_name = forms.CharField(max_length=100, label=_("Last Name"))

    id_number = forms.CharField(max_length=15, label=_("Medicare Number *"),
                                help_text=_("The 9 digit number on your Medicare card."
                                            "We use this to lookup your medical records.")
                                )
    email = forms.EmailField(max_length=75, label=_("Email *"),
                             help_text=_("We will send a verification email to this address."))
    username = forms.CharField(max_length=30, label=_("User Name *"),
                               help_text=_("Choose your desired user name."))
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_("Password (again)"))
    this_is_me_or_agent = forms.CharField(widget=forms.CheckboxInput,
                                          label=_("This is me or I've been given permission to do this *"), required=True,
                                          help_text="I attest the above information is about me "
                                          "or I have been given permission by the person listed "
                                          "to create this account on her or his account. For example,"
                                          "the person above is one of your parents.")
    agree_to_terms = forms.CharField(widget=forms.CheckboxInput,
                                     label=_("Agree *"), required=True,
                                     help_text="I agree to https://www.mymedicare.gov/help/popup/cms-mbp_oswca_popuphelp.aspx")
    human_x = randint(1, 9)
    human_y = randint(1, 9)
    human_z = human_x + human_y
    human_q = ('What is %s + %s?' % (human_x, human_y))
    human = forms.CharField(
        max_length=2,
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

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
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
        try:
            UserRegisterCode.objects.get(used=False, code=invitation_code)
        except:
            raise forms.ValidationError(_('The invitation code is not valid.'))
        return invitation_code

    def save(self):

        invitation_code = self.cleaned_data['invitation_code']
        # make the invitation a invalid/spent.
        invite = UserRegisterCode.objects.get(
            code=str(invitation_code), used=False)

        new_user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'],
            is_active=False)

        UserProfile.objects.create(user=new_user,
                                   user_type="BEN",
                                   create_applications=False,
                                   )
        group = Group.objects.get(name='BlueButton')
        new_user.groups.add(group)

        # Send a verification email
        create_activation_key(new_user)

        invite.used = True
        invite.save()
        return new_user


class UserSignupForm(forms.Form):
    invitation_code = forms.CharField(max_length=30, label=_("Invitation Code"),
                                      help_text=_("While in pilot mode, "
                                                  "an invitation code "
                                                  "is needed to register.")
                                      )
    id_number = forms.CharField(max_length=9, label=_("Medicare Number"),
                                help_text=_("The 9 digit number on your Medicare card."
                                            "Do not provide dashes or spaces. We use this to lookup your medical records.")
                                )
    id_suffix = forms.ChoiceField(choices=MEDICARE_SUFFIX_CHOICES,
                                  help_text=_("The code following your Medicare "
                                              "number on your Medicare card."))

    effective_date_month = forms.ChoiceField(choices=MONTHS.items(),
                                             help_text=_("Effective Month for Part A. "
                                                         "This information can be found on your Medicare card."))

    effective_date_year = forms.CharField(max_length=4,
                                          help_text=_("Effective Month for Part A. "
                                                      "This information can be found on your Medicare card."))
    username = forms.CharField(max_length=30, label=_("User"),
                               help_text=_("Choose your desired user name."))
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

    password1 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=120,
                                label=_("Password (again)"))

    this_is_me_or_agent = forms.CharField(widget=forms.CheckboxInput,
                                          label=_(""), required=True,
                                          help_text="I attest the above information is about me "
                                          "or I have been given permission by the person listed "
                                          "to create this account on her or his account. For example,"
                                          "the person above is one of your parents.")

    primary_care_first_name = forms.CharField(max_length=100,
                                              label=_("Primary Care Physician First Name"))
    primary_care_last_name = forms.CharField(max_length=100,
                                             label=_("Primary Care Physician Last Name"))

    human_x = randint(1, 9)
    human_y = randint(1, 9)
    human_z = human_x + human_y
    human_q = ('What is %s + %s?' % (human_x, human_y))
    human = forms.CharField(
        max_length=2,
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

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
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
        if UserRegisterCode.objects.filter(used=False,
                                           code=invitation_code).count() != 1:
            raise forms.ValidationError(_('The invitation code is not valid.'))
        return invitation_code

    def save(self):

        invitation_code = self.cleaned_data['invitation_code']
        # make the invitation a invalid/spent.
        invite = UserRegisterCode.objects.get(
            code=str(invitation_code), used=False)
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
