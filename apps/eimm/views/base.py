"""
apps.eimm
Experimental Plan B Integration to MyMedicare.gov
Uses RoboBrowser to do a behind the scenes login to MyMedicare.gov
Grab the Blue Button file
Extract a claim number and other information
Make a search to backend and get FHIR Patient/Id

Author: @ekivemark
Based on original work in:
https://github.com/ekivemark/bbofuser/tree/master/apps/getbb

requires: Werkzeug-0.11.10 robobrowser-0.5.3

"""
# import json
import logging

# from collections import OrderedDict
from robobrowser import (RoboBrowser)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe

from apps.cmsblue.cms_parser import (cms_text_read,
                                     parse_lines)
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import pretty_json

from apps.eimm.forms.medicare import Medicare_Connect
from apps.eimm.utils import (split_name,
                             unique_keys)
from apps.eimm.views.progress import get_fhir_claim

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
    # logger.debug("In eimm.mym_login.connect_first:"
    #              "User:%s \nCrosswalk:%s" % (xwalk.user, xwalk))

    if request.POST:
        form = Medicare_Connect(request.POST)
        if form.is_valid():
            if form.cleaned_data['mmg_user'] and form.cleaned_data['mmg_pwd']:
                context = {}
                #  make the call
                # logger.debug("MAKING THE CALL with:",
                #              form.cleaned_data['mmg_user'],
                #              "and ", form.cleaned_data['mmg_pwd'])

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

                # Now we go and get the BlueButton Text file
                mmg_bb = get_bluebutton(request, mmg)

                # mmg_mail = {}
                # logger.debug("Blue Button returned:", mmg_bb)

                mc_prof = {}
                if mmg_bb['status'] == "OK":
                    pretty_name = pretty_json(split_name(mmg['mmg_name']))
                    mc_prof['user'] = mmg['mmg_user']
                    mc_prof['password'] = mmg['mmg_pwd']
                    mc_prof['name'] = mmg['mmg_name']
                    mc_prof['HumanName'] = pretty_name
                    mc_prof['account'] = mmg['mmg_account']
                    # need to check what is returned in mmg_account.

                    messages.success(request,
                                     "Connection succeeded for " +
                                     mc_prof['name'] + "[" +
                                     mc_prof['user'] + "].")

                    # Update the Medicare user name to the Crosswalk
                    if xwalk.mb_user == '':
                        xwalk.mb_user = mc_prof['user']

                    if mmg_bb['status'] == "OK":
                        # We need to save the Blue Button Text
                        # print("We are okay to update mmg_bbdata",
                        #      "\n with ", mmg_bb['mmg_bbdata'][:250])
                        mc_prof['bb_data'] = mmg_bb['mmg_bbdata']

                        # Save the Blue Button text to the Crosswalk
                        xwalk.bb_text = mmg_bb['mmg_bbdata']

                        # Convert the text to JSON
                        result = bb_to_json(request,
                                            mmg_bb['mmg_bbdata'])

                        # logger.debug("BB Conversion:", result)
                        if result['result'] == "OK":
                            mc_prof['bb_json'] = result['mmg_bbjson']

                            mc_prof['email'] = get_bbemail(request,
                                                           mc_prof['bb_json'])
                            mc_prof['profile'] = get_bbprof(request,
                                                            mc_prof['bb_json'])
                            # Extract claims from Blue Button JSON
                            mc_prof['claims'] = getbbclm(request,
                                                         mc_prof['bb_json'])

                            # logger.debug("returned json from xwalk:", result)

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

                return render(request,
                              'eimm/bluebutton_analytics.html',
                              {'content': context,
                               'profile': mc_prof,
                               'profilep': pretty_json(mc_prof['profile']),
                               'claimsp': pretty_json(mc_prof['claims'])
                               })

    else:
        form = Medicare_Connect()

        # logger.debug("setting up the GET:")

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

    # logger.debug("serialized form:", form)

    # submit the form
    rb.submit_form(form)

    # logger.debug("RB:", rb, "\nRB:", rb.__str__())

    browser = RoboBrowser(history=True)
    if browser:
        pass
    # browser.parser = PARSER

    # logger.debug("Browser History:", browser.history,
    #              "\nBrowser parser:", browser.parser,
    #              # "\nPage html:", rb.parsed
    #              )

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

    # logger.debug("RB post sign-in:", rb,
    #              "rb url:", rb.url)

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

    # logger.debug("RB in Get Blue Button:", rb.url,
    #              "================", "rb:", rb.parsed)

    form = rb.get_form()

    # logger.debug("FORM:", form)
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

    # logger.debug("RB:", rb.url)

    bb_file_link = rb.find("a", {"id": "TXTHyperLink"})
    bb_link = bb_file_link.get('href')
    # Now we have the link to the text file
    # We need to add the Medicare site prefix
    # So we can call RobBrowser.
    bb_link = "https://www.mymedicare.gov/" + bb_link
    # logger.debug("Blue Button Link:", bb_file_link,
    #              "\nhref:", bb_link)

    mmg_back['status'] = "OK"
    # <a href="downloadinformation.aspx?SourcePage=BlueButton-Banner&amp;mode=
    # txt&amp;flags=C11111111"
    # id="TXTHyperLink"
    # title="Download TXT"><b>Download TXT</b></a>

    # Get the Blue Button Text file content
    rb.open(bb_link)

    # logger.debug("\np:", rb.find("p").getText())

    # browser = RoboBrowser(history=True)
    # browser.parser = PARSER

    # strip out just the text from inside the html/body/p tag
    mmg_back['mmg_bbdata'] = rb.find('p').getText()

    # logger.debug("Browser History:%s\nBrowser parser:%s"
    #              # "\nPage html:", rb.parsed,
    #              "\nbb_link:%s\nbb_file_link:%s"
    #              # "\nmmg_bbdata:", mmg_back['mmg_bbdata']
    #              % (browser.history, browser.parser, bb_link, bb_file_link,))

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
    # print("============================")
    # print("bb_to_json: bb_blob:")
    # print("============================")
    # print(bb_blob)
    # print("============================")

    if bb_blob is not '':
        # We have something to process
        bb_dict = cms_text_read(bb_blob)

        # logger.debug("bb_dict:", bb_dict)

        json_stuff = parse_lines(bb_dict)

        # logger.debug("json:", json_stuff)
        # logger.debug("Json Length:", len(json_stuff))

        result['mmg_bbjson'] = json_stuff
        result['description'] = "BlueButton converted to json"
        # messages.info(request, result['description'])
        result['result'] = "OK"
    else:
        result['mmg_bbjson'] = {}
        messages.error(request,
                       "Nothing to process [" + xwalk.mmg_bbdata[:80] + "]")

    # print("==================================")
    # print("bb_to_json: mmg_bbjson/json_stuff:")
    # print("==================================")
    # print(pretty_json(result['mmg_bbjson']))
    # print("==================================")

    return result


@login_required
def get_bbemail(request, bb_json):
    """ Get the BB Json file and find email address"""

    email = ''
    if 'patient' in bb_json:
        if 'email' in bb_json['patient']:
            email = bb_json['patient']['email']

    return email


@login_required
def get_bbprof(request, bb_json):
    """ Get Patient Profile section from BB Json file

        "patient": {
        "patient": {
            "patient": "Demographic"
        },
        "source": "MyMedicare.gov",
        "name": "JOHN DOE",
        "dateOfBirth": "19100101",
        "address": {
            "addressType": "",
            "addressLine1": "123 ANY ROAD",
            "addressLine2": "",
            "city": "ANYTOWN",
            "state": "IN",
            "zip": "46250"
        },
        "phoneNumber": [
            "215-248-0684"
        ],
        "email": "rhall@cgifederal.com",
        "medicare": {
            "partAEffectiveDate": "20140201",
            "partBEffectiveDate": "20140201"
        }}

    """

    profile = {}
    if 'patient' in bb_json:
        profile = bb_json['patient']

    return profile


@login_required
def getbbclm(request, bb_json):
    """ Get claims numbers from BB_JSON file

        "claims": [
        {
            "claims": "Claim Summary",
            "claimNumber": "11122233320000",
            "provider": "No Information Available",
            "providerBillingAddress": "",
            "date": {
                "serviceStartDate": "20151010",
                "serviceEndDate": "20151010"
            },
            "charges": {
                "amountCharged": "$135.00",
                "medicareApproved": "$90.45",
                "providerPaid": "$72.36",
                "youMayBeBilled": "$18.09"
            },
            "claimType": "DME",
            "diagnosisCode1": "E785",
            "diagnosisCode2": "M8458XA",
            "category": "Claim Summary",
            "source": "MyMedicare.gov",
            "details": [
                {
                    "details": "Claim Lines for Claim Number",
                    "lineNumber": "1",
                    "dateOfServiceFrom": "20151010",
                    "dateOfServiceTo": "20151010",
                    "procedureCodeDescription": "E0601 - Continuous Positive "
                                                 "Airway Pressure (Cpap) "
                                                 "Device",
                    "modifier1Description": "MS - Six Month Maintenance And "
                                            "Servicing Fee For Reasonable And "
                                            "Necessary Parts And Labor "
                                            "Which Are",
                    "modifier2Description": "KX - Requirements Specified In "
                                            "The Medical Policy Have Been Met",
                    "modifier3Description": "",
                    "modifier4Description": "",
                    "quantityBilledUnits": "1",
                    "submittedAmountCharges": "$135.00",
                    "allowedAmount": "$90.45",
                    "nonCovered": "$44.55",
                    "placeOfServiceDescription": "12 - Home",
                    "typeOfServiceDescription": "R - Rental of DME",
                    "renderingProviderNo": "DMEPROVIDR",
                    "renderingProviderNpi": "9999999903",
                    "category": "Claim Lines for Claim Number",
                    "source": "MyMedicare.gov",
                    "claimNumber": "11122233320000"
                }]}

    """

    claim_info = []
    if 'claims' in bb_json:
        for claim in bb_json['claims']:
            claim_summary = {}
            if 'claimNumber' in claim:
                claim_summary['claimNumber'] = claim['claimNumber']
            else:
                claim_summary['claimNumber'] = ''
            if 'provider' in claim:
                claim_summary['provider'] = claim['provider']
            else:
                claim_summary['provider'] = ''
            if 'date' in claim:
                claim_summary['date'] = claim['date']
            else:
                if 'serviceStartDate' in claim:
                    service_start = claim['serviceStartDate']
                else:
                    service_start = ''
                if 'serviceEndDate' in claim:
                    service_end = claim['serviceEndDate']
                else:
                    service_end = ''
                claim_summary['date'] = {'serviceStartDate': service_start,
                                         'serviceEndDate': service_end}
            claim_info.append(claim_summary)

    return claim_info


def eval_claims(request, claims):
    """ Receive Claims and make call to backend to match claims

        param: claims = [{"claimNumber": "",
                          "provider": "",
                          "date": {"serviceStartDate": "",
                                   "serviceEndDate": ""}}]

        param: patient = "patient": {
        "patient": {
            "patient": "Demographic"
        },
        "source": "MyMedicare.gov",
        "name": "JOHN DOE",
        "dateOfBirth": "19100101",
        "address": {
            "addressType": "",
            "addressLine1": "123 ANY ROAD",
            "addressLine2": "",
            "city": "ANYTOWN",
            "state": "IN",
            "zip": "46250"
        },
        "phoneNumber": [
            "215-248-0684"
        ],
        "email": "rhall@cgifederal.com",
        "medicare": {
            "partAEffectiveDate": "20140201",
            "partBEffectiveDate": "20140201"
        }}


    """

    fhir_claims = []
    for claim in claims:
        if claim['claimNumber']:
            fhir_claim = get_fhir_claim(request, claim['claimNumber'])
            if fhir_claim['found']:
                fhir_claims.append(fhir_claim)

    # Now we look at Patient Information
    # Do all claims refer to same Patient Id?
    # Create a short list
    # patient_ids = unique_keys(fhir_claims, key="patient")
    # print("Patient ID List:", patient_ids)

    # patient_match = check_patient(fhir_claim['patient'],
    #                               patient)

    return fhir_claims


@login_required
def convert_bb(request):
    """ Read bb_text from CrossWalk
        Convert to JSON (bb_to_json)
        Analyze JSON
        Get Claims
        Search for Claims
        Check for Unique Patient
        Get Unique Patient
        Store ID in Crosswalk

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

    # Do we have Blue Button text to work with?
    if not xwalk.bb_text:
        return HttpResponseRedirect(reverse('home'))

    # Convert from text to JSON
    bb_result = bb_to_json(request, xwalk.bb_text)
    bb_json = bb_result['mmg_bbjson']
    # print("JSON:", bb_result['mmg_bbjson'])

    # Extract Claims from bb_json
    bb_claims = getbbclm(request, bb_result['mmg_bbjson'])
    # print("\nClaims:", bb_claims)

    fhir_claims = eval_claims(request, bb_claims)

    # Take bb_claims and get a unique list of patients
    # Hopefully we only have ONE
    bb_patient_ids = unique_keys(fhir_claims, key="patient")
    # print("Patient IDs:", bb_patient_ids)

    if len(bb_patient_ids) is 0:
        # We have a problem...
        # Too many or Too Few Patient IDs returned from Claims

        messages.error(request, "Unable to find a Patient Match")
    elif len(bb_patient_ids) > 1:
        messages.error(request, "Unable to match to a unique Patient ID")
    else:
        messages.info(request, "We found a match %s" % bb_patient_ids[0])
        if not xwalk.fhir_id:
            # We need the Id from Patient ID
            # It should be in format Patient/{ID}
            fhir_id = bb_patient_ids[0].split('/')
            if len(fhir_id) > 1:
                fhir_id_num = fhir_id[-1]
                xwalk.fhir_id = fhir_id_num
                mc_prof = {}
                if bb_json['result'] == "OK":
                    mc_prof['bb_json'] = bb_json['mmg_bbjson']

                    mc_prof['email'] = get_bbemail(request,
                                                   bb_json)
                    mc_prof['profile'] = get_bbprof(request,
                                                    bb_json)
                    # Extract claims from Blue Button JSON
                    mc_prof['claims'] = getbbclm(request,
                                                 bb_json)
                    return render(request,
                                  'eimm/bluebutton_analytics.html',
                                  {'content': bb_json,
                                   'profile': mc_prof,
                                   'profilep': pretty_json(mc_prof['profile']),
                                   'claimsp': pretty_json(mc_prof['claims'])
                                   })

    return HttpResponseRedirect(reverse('home'))
