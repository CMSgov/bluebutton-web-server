from django.conf import settings
from django.contrib.auth.models import User, Group
from robobrowser import RoboBrowser
from .models import UserProfile


class MyMedicareBackend(object):
    """
    Authenticate against MyMedicare.gov via screen scrape.
    login_url = 'https://www.mymedicare.gov/default.aspx'
    """
    def authenticate(self, username=None, password=None):
        login_url = 'https://www.mymedicare.gov/default.aspx'
        rb = RoboBrowser()
        rb.parser = 'lxml'
        rb.open(login_url)
        # Get the form content
        form = rb.get_form()
        if settings.DEBUG:
            print("Page:", rb)
        # We will be working with these form fields.
        # Set them as variables for easier re-use
        form_pwd = "ctl00$ContentPlaceHolder1$ctl00$HomePage$SWEPassword"
        form_usr = "ctl00$ContentPlaceHolder1$ctl00$HomePage$SWEUserName"
        form_agree = "ctl00$ContentPlaceHolder1$ctl00$HomePage$Agree"
        form_create_acc = "ctl00$ContentPlaceHolder1$ctl00$HomePage$lnk" \
                          "CreateAccount"
        # Set the form field values
        form.fields[form_usr].value = username
        form.fields[form_pwd].value = password
        # There is a javascript popup after hitting submit
        # that the form_agree to  "True"
        # Default in form is "False"
        form.fields[form_agree].value = "True"
        # Remove the CreateAccount field. It seems to drive the form
        # to the registration page.
        form.fields.pop(form_create_acc)
        # Capture the dynamic elements from these damned aspnetForms
        # We need to feed them back to allow the form to validate
        VIEWSTATEGENERATOR = form.fields['__VIEWSTATEGENERATOR']._value
        EVENTVALIDATION = form.fields['__EVENTVALIDATION']._value
        VIEWSTATE = form.fields['__VIEWSTATE']._value
        # Set the validator fields back in to the form
        form.fields['__VIEWSTATEGENERATOR'].value = VIEWSTATEGENERATOR
        form.fields['__VIEWSTATE'].value = VIEWSTATE
        form.fields['__EVENTVALIDATION'].value = EVENTVALIDATION
        # Prepare the form for submission
        form.serialize()
        # submit the form
        rb.submit_form(form)
        # If the login was successful then we would be redirected to the dashboard.
        if rb.url == "https://www.mymedicare.gov/dashboard.aspx":
            """The login worked."""
            # Get the name
            my_name = rb.find("li", {"id": "welcomeli"})
            if my_name:
                my_name = my_name.contents[0].replace("Welcome, ", "")

            split_name = my_name.split(' ')
            first_name = split_name[0]
            last_name = split_name[-1]
            if not last_name:
                last_name = split_name[-2]

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password
                # to anything, because it won't be checked; the password
                # from the external backend is checked (coming from settings).
                user = User(username=username, password='flubbernubber',
                            first_name=first_name,
                            last_name=last_name)
                user.save()
                up, created = UserProfile.objects.get_or_create(user=user,
                                                                user_type='BEN')
                group = Group.objects.get(name='BlueButton')
                user.groups.add(group)

            return user
        # The MyMedicare login failed.
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
