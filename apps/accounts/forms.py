from random import randint

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext_lazy as _

from .models import Invitation, RequestInvite, UserProfile, create_activation_key


class RequestDeveloperInviteForm(forms.ModelForm):
    class Meta:
        model = RequestInvite
        fields = ('first_name', 'last_name', 'organization', 'email')

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
        if str(human) != str(self.human_z):
            raise forms.ValidationError(_('You are either not human or '
                                          'just just really bad at math.'))
        return human


class RequestUserInviteForm(forms.ModelForm):
    class Meta:
        model = RequestInvite
        fields = ('first_name', 'last_name', 'email')

    user_type = 'BEN'
    human_x = randint(1, 9)
    human_y = randint(1, 9)
    human_z = human_x + human_y
    human_q = ('What is %s + %s?' % (human_x, human_y))
    human = forms.CharField(
        max_length=30,
        label=_(human_q),
        help_text='We are asking this to make sure you are human. '
                  'Hint: the answer is %s.' % human_z
    )
    required_css_class = 'required'

    def clean_human(self):
        human = self.cleaned_data.get('human', '')
        if str(human) != str(self.human_z):
            raise forms.ValidationError(_('You are either not human or '
                                          'just just really bad at math.'))
        return human


class PasswordResetRequestForm(forms.Form):
    email = forms.CharField(max_length=75, label=_('Email'))
    required_css_class = 'required'


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_('Password*'))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=30,
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
    password = forms.CharField(widget=forms.PasswordInput, max_length=30,
                               label=_('Password'))
    required_css_class = 'required'


class SignupUserForm(forms.Form,):

    invitation_code = forms.CharField(max_length=30,
                                      label=_("Invitation Code"))
    username = forms.CharField(max_length=30, label=_("User"))
    email = forms.EmailField(max_length=75, label=_("Email"))
    first_name = forms.CharField(max_length=100, label=_("First Name"))
    last_name = forms.CharField(max_length=100, label=_("Last Name"))

    # organization_name is not rquired for Beneficiary
    # organization_name  = forms.CharField(max_length=100,
    #                                      label=_("Organization Name"),
    #                                      required=False
    #                                      )
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_('Password'))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_('Password (again)'))
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

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if email:
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(username=username).count():
                raise forms.ValidationError(_('This email address '
                                              'is already registered.'))
            return email
        else:
            return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
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
            is_active=False,
        )

        UserProfile.objects.create(user=new_user,
                                   user_type='BEN')

        group = Group.objects.get(name='BlueButton')
        new_user.groups.add(group)

        # Send a verification email
        create_activation_key(new_user)

        return new_user


class SignupDeveloperForm(forms.Form, ):
    invitation_code = forms.CharField(max_length=30, label=_("Invitation Code")
                                      )
    username = forms.CharField(max_length=30, label=_("User"))
    email = forms.EmailField(max_length=75, label=_("Email"))
    first_name = forms.CharField(max_length=100, label=_("First Name"))
    last_name = forms.CharField(max_length=100, label=_("Last Name"))

    organization_name = forms.CharField(max_length=100,
                                        label=_("Organization Name"),
                                        required=False
                                        )
    password1 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password (again)"))

    required_css_class = 'required'

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
            return email
        else:
            return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
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
                                   organization_name=self.cleaned_data['organization_name'],
                                   user_type="DEV")

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
    organization_name = forms.CharField(max_length=100,
                                        label=_('Organization Name'),
                                        required=False)
    required_css_class = 'required'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if email and User.objects.filter(email=email).exclude(email=email).count():
                raise forms.ValidationError(_('This email address is '
                                              'already registered.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exclude(username=username).count():
            raise forms.ValidationError(_('This username is already taken.'))
        return username
