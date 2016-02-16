#!/usr/bin/env python
from django import forms
from django.utils.translation import ugettext_lazy as _


class BeneficaryApplicationDeveloperSignupForm(forms.Form):
    
    username        = forms.CharField(max_length=30, label=_("User"))
    email           = forms.EmailField(max_length=75, label=_("Email"))
    first_name      = forms.CharField(max_length=100, label=_("First Name"))
    last_name       = forms.CharField(max_length=100, label=_("Last Name"))
    organization_name  = forms.CharField(max_length=100, label=_("Organization Name"))
    password1       = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password"))
    password2       = forms.CharField(widget=forms.PasswordInput, max_length=30,
                                label=_("Password (again)"))
    human = forms.CharField(max_length=30, label=_("What is 6 + 1?"),
            help_text = "We are asking this to make sure you are human. Hint: the answer is 7.")
     
     
    required_css_class = 'required'
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        if len(password1) < settings.MIN_PASSWORD_LEN:
            msg=_("Password must be at least %s characters long.  Be tricky!") % (settings.MIN_PASSWORD_LEN)
            raise forms.ValidationError(msg)
        return password2
    
    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        if email:
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(username=username).count():
                raise forms.ValidationError(_('This email address is already registered.'))
            return email
        else:
            return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).count()>0:
            raise forms.ValidationError(_('This username is already taken.'))
        return username

    def save(self):
        
        invitation_code = self.cleaned_data['invitation_code']
        #make the invitation a invalid/spent.
        invite = Invitation.objects.get(code=str(invitation_code), valid=True)
        invite.valid=False
        invite.save()
        
        new_user = User.objects.create_user(
                        username=self.cleaned_data['username'],
                        first_name=self.cleaned_data['first_name'],
                        last_name=self.cleaned_data['last_name'],
                        password=self.cleaned_data['password1'],
                        email=self.cleaned_data['email'])
        
        up = UserProfile.objects.create(user=new_user,
                                        organization_name=self.cleaned_data['organization_name'])         

        
        return new_user