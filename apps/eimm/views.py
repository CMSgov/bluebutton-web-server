"""
apps.eimm
Experimental Plan B Integration to MyMedicare.gov
Uses RoboBrowser to do a behind the scenes login to MyMedicare.gov
Grab the BlueButton file
Extract a claim number and other information
Make a search to backend and get FHIR Patient/Id

Author: @ekivemark
Based on original work in:
https://github.com/ekivemark/bbofuser/tree/master/apps/getbb

requires: Werkzeug-0.11.10 robobrowser-0.5.3

"""
import logging

from robobrowser import (RoboBrowser)

# from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.utils.safestring import mark_safe


from apps.cmsblue.cms_parser import (cms_text_read,
                                     parse_lines)
from apps.fhir.bluebutton.models import Crosswalk

from .forms.medicare import Medicare_Connect

logger = logging.getLogger('hhs_server.%s' % __name__)

# BeautifulSoup
BS_PARSER = 'lxml'


@login_required
def connect_first(request):
    """
    Prompt for MyMedicare.gov user and password
    Ask for confirmation to connect to MyMedicare.gov

    call connect with userid and password

    :param request:
    :return:
    """

    try:
        xwalk = Crosswalk.objects.get(user=request.user)
    except Crosswalk.DoesNotExist:
        xwalk = Crosswalk()
        xwalk.user = request.user
        # We may want to add the default FHIR Server to the crosswalk entry
        # before we save.
        # xwalk.fhir_source =
        xwalk.save()

    xwalk = Crosswalk.objects.get(user=request.user)

    form = Medicare_Connect()
    logger.debug("In eimm.mym_login.connect_first\n",
                 "User:", xwalk.user,
                 "\nCrosswalk:", xwalk)

    if request.POST:
        form = Medicare_Connect(request.POST)
        if form.is_valid():
            if form.cleaned_data['mmg_user'] and form.cleaned_data['mmg_pwd']:
                context = {}
                #  make the call
                logger.debug("MAKING THE CALL with:",
                             form.cleaned_data['mmg_user'],
                             "and ", form.cleaned_data['mmg_pwd'])

                mmg = {}
                mmg['mmg_user'] = form.cleaned_data['mmg_user']
                mmg['mmg_pwd'] = form.cleaned_data['mmg_pwd']

                # see if the call works
                mmg = connect(request, mmg)

                if mmg['status'] == 'FAIL':
                    # we had a problem with login
                    messages.info(request,
                                  mark_safe("Do you need to connect to "
                                            "<a href='https://mymedicare.gov'"
                                            " target='_blank'>"
                                            "MyMedicare.gov</a> to check your"
                                            " account?"))
                    return render(request,
                                  'eimm/medicare_connect.html',
                                  {'form': form})

                mmg_bb = get_bluebutton(request, mmg)

                # mmg_mail = {}
                logger.debug("BlueButton returned:", mmg_bb)

                medicare_profile = {}
                if mmg_bb['status'] == "OK":
                    medicare_profile['user'] = mmg['mmg_user']
                    medicare_profile['password'] = mmg['mmg_pwd']
                    medicare_profile['name'] = mmg['mmg_name']
                    medicare_profile['account'] = mmg['mmg_account']

                    # Update the Medicare user name to the Crosswalk
                    if xwalk.mb_user == '':
                        xwalk.mb_user = medicare_profile['user']

                    if mmg_bb['status'] == "OK":
                        # We need to save the BlueButton Text
                        # print("We are okay to update mmg_bbdata",
                        #      "\n with ", mmg_bb['mmg_bbdata'][:250])
                        medicare_profile['bb_data'] = mmg_bb['mmg_bbdata']

                        result = bb_to_json(request,
                                            mmg_bb['mmg_bbdata'])
                        logger.debug("BB Conversion:", result)
                        if result['result'] == "OK":
                            medicare_profile['bb_json'] = result['mmg_bbjson']
                            logger.debug("returned json from xwalk:",
                                         medicare_profile['bb_json'])

                        #     for key, value in xwalk.mmg_bbjson.items():
                        #         # print("Key:", key)
                        #         if key == "patient":
                        #             for k, v in value.items():
                        #                 # print("K:", k, "| v:", v)
                        #                 if k == "email":
                        #                     xwalk.mmg_email = v
                        # if not xwalk.mmg_bbfhir:
                        #     if result['result'] == "OK":
                        #         outcome = json_to_eob(request)
                        #         if outcome['result'] == "OK":
                        #             xwalk.mmg_bbfhir = True

                    # if mmg_mail['status'] == "OK":
                    #     xwalk.mmg_email = mmg_mail['mmg_email']

                    # Save the Crosswalk changes
                    xwalk.save()

                    context['mmg'] = mmg

                return HttpResponseRedirect(reverse('home'),
                                            RequestContext(request), context)

    else:
        form = Medicare_Connect()

        logger.debug("setting up the GET:")

    return render(request,
                  'eimm/medicare_connect.html',
                  {'form': form})


@login_required
def connect(request, mmg):
    """
    Login to MyMedicare.gov using RoboBrowser
    :param request:
    :param username:
    :param password:
    :return:

    """
    mmg_back = mmg
    mmg_back['status'] = "FAIL"
    PARSER = BS_PARSER
    if not PARSER:
        logger.debug('Default Parser for BeautifulSoup:', 'lxml')
        PARSER = 'lxml'

    login_url = 'https://www.mymedicare.gov/default.aspx'

    # This is for testing. Next step is to receive as parameters
    username = mmg['mmg_user']  # 'MBPUSER202A'
    # password = 'BadPassw'# 'CMSPWD2USE'
    password = mmg['mmg_pwd']  # 'CMSPWD2USE'

    # Call the default page
    # We will then want to get the Viewstate and eventvalidation entries
    # we need to submit them with the form
    rb = RoboBrowser()
    mmg_back['robobrowser'] = rb

    # Set the default parser (lxml)
    # This avoids BeautifulSoup reporting an issue in the console/log
    rb.parser = PARSER

    # Open the form to start the login
    rb.open(login_url)

    # Get the form content
    form = rb.get_form()

    # if settings.DEBUG:
    #    print("Page:", rb)

    # We will be working with these form fields.
    # Set them as variables for easier re-use
    form_pwd = "ctl00$ContentPlaceHolder1$ctl00$HomePage$SWEPassword"
    form_usr = "ctl00$ContentPlaceHolder1$ctl00$HomePage$SWEUserName"
    form_agree = "ctl00$ContentPlaceHolder1$ctl00$HomePage$Agree"
    # sign_in = "ctl00$ContentPlaceHolder1$ctl00$HomePage$SignIn"
    # EVENTTARGET = "ctl00$ContentPlaceHolder1$ctl00$HomePage$SignIn"
    form_create_acc = "ctl00$ContentPlaceHolder1$ctl00$HomePage$lnk" \
                      "CreateAccount"

    # Set the form field values
    form.fields[form_usr].value = username
    form.fields[form_pwd].value = password

    # There is a javascript popup after hitting submit
    # It seems to set the following field to "True"
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

    # if settings.DEBUG:
    #     print("EventValidation:", EVENTVALIDATION )
    #     print("ViewStateGenerator:", VIEWSTATEGENERATOR)

    # Set the validator fields back in to the form
    form.fields['__VIEWSTATEGENERATOR'].value = VIEWSTATEGENERATOR
    form.fields['__VIEWSTATE'].value = VIEWSTATE
    form.fields['__EVENTVALIDATION'].value = EVENTVALIDATION

    # Prepare the form for submission
    form.serialize()

    logger.debug("serialized form:", form)

    # submit the form
    rb.submit_form(form)

    logger.debug("RB:", rb, "\nRB:", rb.__str__())

    browser = RoboBrowser(history=True)
    # browser.parser = PARSER

    logger.debug("Browser History:", browser.history,
                 "\nBrowser parser:", browser.parser,
                 # "\nPage html:", rb.parsed
                 )

    if not rb.url == "https://www.mymedicare.gov/dashboard.aspx":
        err_msg = rb.find("span",
                          {"id": "ctl00_ContentPlaceHolder1"
                                 "_ctl00_HomePage_lblError"})
        if err_msg:
            err_msg = err_msg.contents
            messages.error(request, err_msg)
        messages.error(request, "We had a problem connecting to your"
                                "Medicare account")
        mmg_back['status'] = "FAIL"
        mmg_back['url'] = rb.url
        return mmg_back

    # <ul id="headertoolbarright">
    #    <li class="welcometxt" id="welcomeli">Welcome, JOHN A DOE </li>
    my_name = rb.find("li", {"id": "welcomeli"})
    if my_name:
        my_name = my_name.contents[0].replace("Welcome, ", "")
    my_account = rb.find("div", {"id": "RightContent"})
    if my_account:
        my_account = my_account.prettify()
        my_account = my_account.replace('href="/',
                                        'target="_blank" '
                                        'href="https://www.mymedicare.gov/')
        # my_account = my_account.contents
    # href="/mymessages.aspx"
    # href="/myaccount.aspx"
    # href="/plansandcoverage.aspx"
    # my_account.str('href="/mymessages.aspx',
    #                'href="https://www.mymedicare.gov/mymessages.apsx')
    # my_account.str('href="/myaccount.aspx',
    #                'href="https://www.mymedicare.gov/myaccount.aspx')
    # my_account.str('href="/plansandcoverage.aspx',
    #                'href="https://www.mymedicare.gov/plansandcoverage.aspx')

    # if settings.DEBUG:
    #     print("\nMyAccount:", len(my_account), "|", my_account)

    # Need to pass data to context and then render to different
    # template with some data retrieved from MyMedicare.gov
    # If successfully logged in, Or return an error message.
    mmg_back['status'] = "OK"
    mmg_back['url'] = rb.url
    mmg_back['mmg_account'] = my_account
    mmg_back['mmg_name'] = my_name

    mmg_back['robobrowser'] = rb

    logger.debug("RB post sign-in:", rb,
                 "rb url:", rb.url)

    return mmg_back


@login_required
def get_bluebutton(request, mmg):
    """

    :param request:
    :param mmg:
    :return:

    """

    # mmg will contain 'robobrowser'

    mmg_back = mmg
    mmg_back['status'] = "FAIL"

    # <input type="image" name="ibBB" id="ibBB"
    # title="Download my data - Opens in a new window"
    # class="ibBB"
    # src="/images/bluebutton_breadcrumb.png"
    # alt="Blue Button - Download My Data. Opens in a new window."
    # onclick="javascript:window.open('/DownloadMyData.aspx?SourcePage=Banner',
    # '_blank',
    # 'location=no,scrollbars=yes,resizable=yes');return false;"
    # style="height:30px;width:123px;border-width:0px;">

    target_page = "https://www.mymedicare.gov/DownloadMyData.aspx?" \
                  "SourcePage=Banner"

    PARSER = BS_PARSER
    if not PARSER:
        logger.debug('Default Parser for BeautifulSoup:', 'lxml')
        PARSER = 'lxml'

    # Call the default page
    rb = mmg['robobrowser']
    # rb = RoboBrowser(history=True)

    # current_page = rb.url
    print("currently on:", rb.url)

    # Set the default parser (lxml)
    # This avoids BeautifulSoup reporting an issue in the console/log
    rb.parser = PARSER
    rb.open(target_page)

    logger.debug("RB in Get BlueButton:", rb.url,
                 "================", "rb:", rb.parsed)

    form = rb.get_form()

    logger.debug("FORM:", form)
    # <form name="formMyMedicare"
    # method="post"
    # action="applets/BlueButton/bluebuttonresp.aspx?guid=
    #         97290573-7965-11DF-93F2-0800200C9A66"
    # id="formMyMedicare"
    # autocomplete="off">

    # Capture the dynamic elements from these damned aspnetForms
    # We need to feed them back to allow the form to validate
    VIEWSTATEGENERATOR = form.fields['__VIEWSTATEGENERATOR']._value
    EVENTVALIDATION = form.fields['__EVENTVALIDATION']._value
    VIEWSTATE = form.fields['__VIEWSTATE']._value

    # Set the validator fields back in to the form
    form.fields['__VIEWSTATEGENERATOR'].value = VIEWSTATEGENERATOR
    form.fields['__VIEWSTATE'].value = VIEWSTATE
    form.fields['__EVENTVALIDATION'].value = EVENTVALIDATION

    # <input id="rbtnAllType"
    # type="radio"
    # name="TypeSelectRange"
    # value="rbtnAllType"
    # /><label
    # for="rbtnAllType">
    form.fields['ServiceDateRange'].value = "months36"
    form.fields['TypeSelectRange'].value = "rbtnAllType"
    # form.fields['chkClaims'].value = "1"
    # form.fields['chkDrugs'].value = "1"
    # form.fields['chkEmerContact'].value = "1"
    # form.fields['chkFamilyHistory'].value = "1"
    # form.fields['chkPharmacies'].value = "1"
    # form.fields['chkPlans'].value = "1"
    # form.fields['chkPreventiveServices'].value = "1"
    # form.fields['chkSelfReportedInfo'].value = "1"
    # name="ServiceDateRange" value="months36"
    # form.fields['rbtnSelectType'].value = "rdoMonths36"

    # <input id="chkAgree"
    # type="checkbox"
    # name="chkAgree">
    form.fields['chkAgree'].value = "on"
    # <input type="submit"
    # name="btnSubmit"
    # value="Submit"
    # id="btnSubmit"
    # title="Blue Button - Download My Data.  Opens in a new dialog."
    # class="btn-primary BBsubmit"
    # data-validationtrigger="" />
    #
    # <!--<input type="submit"
    # name="Button1"
    # value="Submit"
    # id="Button1"
    # title="Blue Button - Download My Data.  Opens in a new dialog."
    # class="btn-primary BBsubmit" />  -->
    form.fields['inpScreenWidth'].value = "1011"
    # form.fields['__EVENTTARGET'].value = "btnSubmit"

    form.fields.pop('btnReset')
    form.fields.pop('btnCancel')

    form.fields['btnSubmit'].value = "Submit"

    form.serialize()

    rb.submit_form(form)

    logger.debug("RB:", rb.url)

    bb_file_link = rb.find("a", {"id": "TXTHyperLink"})
    bb_link = bb_file_link.get('href')
    # Now we have the link to the text file
    # We need to add the Medicare site prefix
    # So we can call RobBrowser.
    bb_link = "https://www.mymedicare.gov/" + bb_link
    logger.debug("BlueButton Link:", bb_file_link,
                 "\nhref:", bb_link)

    mmg_back['status'] = "OK"
    # <a href="downloadinformation.aspx?SourcePage=BlueButton-Banner&amp;mode=
    # txt&amp;flags=C11111111"
    # id="TXTHyperLink"
    # title="Download TXT"><b>Download TXT</b></a>

    # Get the BlueButton Text file content
    rb.open(bb_link)

    logger.debug("\np:", rb.find("p").getText())

    browser = RoboBrowser(history=True)
    # browser.parser = PARSER

    # strip out just the text from inside the html/body/p tag
    mmg_back['mmg_bbdata'] = rb.find('p').getText()

    logger.debug("Browser History:", browser.history,
                 "\nBrowser parser:", browser.parser,
                 # "\nPage html:", rb.parsed,
                 "\nbb_link:", bb_link,
                 "\nbb_file_link:", bb_file_link,
                 "\nmmg_bbdata:", mmg_back['mmg_bbdata'])

    return mmg_back


@login_required
def bb_to_json(request, bb_blob=''):
    """
    Get the User's Crosswalk record
    Get the mmg_bbdata textfield
    Convert to json
    Update mmg_bbjson

    :param request:
    :return:
    """
    result = {}
    result['result'] = "FAIL"

    xwalk = Crosswalk.objects.get(user=request.user)

    if bb_blob is not '':
        # We have something to process
        bb_dict = cms_text_read(bb_blob)

        logger.debug("bb_dict:", bb_dict)

        json_stuff = parse_lines(bb_dict)

        logger.debug("json:", json_stuff)
        logger.debug("Json Length:", len(json_stuff))

        result['mmg_bbjson'] = json_stuff
        result['description'] = "BlueButton converted to json and saved"
        messages.info(request, result['description'])
        result['result'] = "OK"
    else:
        messages.error(request,
                       "Nothing to process [" + xwalk.mmg_bbdata[:80] + "]")

    return result
