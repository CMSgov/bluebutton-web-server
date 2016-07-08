#!/usr/bin/env python
"""
convert bluebutton to json
"""
import collections
from apps.cmsblue.cms_parser import *
from apps.cmsblue.file_def_cms import *

# inPath="va_sample_file.txt"
# OutPath="va_sample_file.json"

sections = ("MYMEDICARE.GOV PERSONAL HEALTH INFORMATION",
            "DEMOGRAPHIC",
            "MY HEALTHEVET PERSONAL HEALTH INFORMATION",
            "MY HEALTHEVET ACCOUNT SUMMARY",
            "DEMOGRAPHICS",
            "ALLERGIES/ADVERSE REACTIONS",
            "MEDICAL EVENTS",
            "IMMUNIZATIONS",
            "FAMILY HEALTH HISTORY",
            "MILITARY HEALTH HISTORY",
            "VA MEDICATION HISTORY",
            "MEDICATIONS AND SUPPLEMENTS",
            "VA WELLNESS REMINDERS",
            "VITALS AND READINGS")

section_info = [
    {"MYMEDICARE.GOV PERSONAL "
     "HEALTH INFORMATION": {"title": "MyMedicare.gov Personal Health "
                                     "Information",
                            "languageCode": "code=\"en-US\"",
                            "versionNumber": {"value": "3"},
                            "effectiveTime": {"value": "20150210171504+0500"},
                            "confidentialityCode": {"code": "N",
                                                    "codeSystem": "2.16.840.1."
                                                                  "113883."
                                                                  "5.25"},
                            "originator": "MyMedicare.gov"}}]

divider = "----------"
vitals = ("Blood pressure", "Body weight")

#          get segment.filetype (eg. CMS or VA)
#          get segment.prefill_content for segment
#          get segment.level (ie. header = 0)
#          get segment.name
#          get segment.key_match_end
#          get segment.prefix

seg = [{"key": "MYMEDICARE.GOV PERSONAL HEALTH INFORMATION",
        "prefill": {"title": "MyMedicare.gov Personal Health Information",
                    "languageCode": "code=\"en-US\"",
                    "versionNumber": {"value": "3"},
                    "effectiveTime": {"value": "20150210171504+0500"},
                    "confidentialityCode": {"code": "N",
                                            "codeSystem": "2.16.840.1."
                                                          "113883.5.25"},
                    "originator": "MyMedicare.gov"},
        "level": 0,
        "name": "header",
        "end_match": "---------",
        "file_source": "CMS",
        },
       {"key": "Demographic",
        "prefill": {},
        "level": 0,
        "name": "patient",
        "end_match": "Part B Effective Date",
        "file_source": "CMS",
        },
       {"key": "Emergency Contact",
        "prefill": {},
        "level": 0,
        "name": "emergency_contact",
        "end_match": "---------",
        "file_source": "CMS",
        },
       {"key": "emergency_contact.Contact Name",
        "prefill": {},
        "level": 1,
        "list": True,
        "name": "",
        "end_match": "Email Address",
        "file_source": "CMS",
        },
       {"key": "emergency_contact.Contact Name.",
        "prefill": {},
        "level": 2,
        "dictionary": True,
        "name": "address",
        "end_match": "zip",
        "file_source": "CMS",
        }]


def age(dob):
    import datetime
    today = datetime.date.today()

    if today.month < dob.month or (today.month == dob.month and
                                   today.day < dob.day):
        return today.year - dob.year - 1
    else:
        return today.year - dob.year


def simple_parse(inPath):
    line = []
    items = []
    generic_dict = collections.OrderedDict()
    with open(inPath, 'r') as f:
        for i, l in enumerate(f):
            generic_dict = {}
            line = l.split(":")
            if len(line) > 1:
                k = line[0]
                v = line[1]
                if len(k) > 1:
                    # do we have a date and time
                    k = "Date"

                if v[0] == " ":
                    v = v.lstrip()
                if len(line) > 2 and k == "Time":
                    v = "%s:%s" % (line[1], line[2])
                v = v.rstrip()
                generic_dict[k] = v

                items.append(generic_dict)
    f.close()
    return items


def section_parse(inPath):
    # print("in Section Parse")
    # line = []
    # items = []
    # generic_dict = collections.OrderedDict()
    segments = collections.OrderedDict()
    segment_open = False
    current_segment = ""
    segment_dict = collections.OrderedDict()
    segment_source = ""

    with open(inPath, 'r') as f:
        for i, l in enumerate(f):
            generic_dict = {}
            # print("input: %s" % l)
            line = l.split(":")
            if len(line) > 1:
                k = line[0]
                v = line[1]
                print("Line %s: %s" % (i, line))
                if v[0] == " ":
                    v = v.lstrip()
                v = v.rstrip()
                segment_source = set_source(segment_source, k, v)
                if k.upper() == "SOURCE":
                    v = segment_source
                if current_segment == "header":
                    if k[2] == "/":
                        print("got the date line")
                        v = {"value": parse_time(l)}
                        k = "effectiveTime"
                generic_dict[k] = v
                segment_dict[k] = v
                segments.update({current_segment: segment_dict})
                # print("Segments-current_segment: %s" % current_segment)
                # print(segments[current_segment])
                # print("*******")

            else:
                # print("Line: %s Not processed" % i)
                if divider in l:
                    if segment_open:
                        segment_open = False
                    else:
                        segment_open = True
                if (divider not in l) and (segment_open is True):
                    l = l.strip()
                    if len(l) <= 1:
                        l = "Claim"
                    current_segment, segment_dict = segment_eval(l.strip())

    f.close()
    return segments


def bb_file_parse(inPath):
    # Parse a CMS Blue Button text file
    # Using a redefined Parsing process

    # Set default variables on entry
    k = " "
    v = " "
    # line = []
    items = collections.OrderedDict()
    header_line = False
    close_segment = False
    # segments = collections.OrderedDict()
    # segment_open = False
    current_segment = ""
    segment_dict = collections.OrderedDict()
    segment_source = ""
    generic_dict = collections.OrderedDict()
    # drill_down = ""
    # sub_list = []

    # Use collections.OrderedDict() to retain line sequencing
    # line_dict = collections.OrderedDict()

    # Open the file for reading
    with open(inPath, 'r') as f:

        # get the line from the input file
        for i, l in enumerate(f):
            # reset the line_dict to blank
            # line_dict = collections.OrderedDict()
            # determine if we are dealing with a header
            # headers start with "--------------------------------"
            l = l.rstrip()
            # print("Line [%s:%s]" % (i,l))

            line = l.split(":")
            if len(line) > 1:
                k = line[0]
                v = line[1].lstrip()
                v = v.rstrip()

            # ===================
            # Temporary Insertion
            # if i > 80:
            #    break
            # end of temporary insertion
            # ===================

            if len(l) <= 1 and header_line is False:
                # The line is a detail line and is empty so ignore
                # it and move on to next line
                # print("empty line %s[%s] - skipping to next line" % (i,l))
                continue

            print("Line [%s:%s]" % (i, l))
            # From now on We are dealing with a non-blank line
            # Segment titles are wrapped by lines of minus signs (divider)
            # So let's check if we have found a divider
            if divider in l:
                # A divider is either opening a title or closing it
                # If header_line is True then this must be closing a header
                # and we are about to start writing segment details
                if header_line:
                    # we must have written the title because this is the
                    # second divider line
                    # so set header_line=False and skip to the next line
                    # print "Setting header_line=False"
                    header_line = False
                    continue
                else:
                    # If header_line is False we must be opening a header
                    # So the next line should be the segment title
                    # but first we need to write out the last segment
                    # set the header_line=True
                    header_line = True

                    # if close_segment:
                    if True:
                        # print(current_segment)
                        if i > 3:
                            # if close_segment is set we need to
                            # write the dict to items
                            print("Write Hdr segment: %s" % current_segment)
                            # print(segment_dict)
                            items[current_segment] = segment_dict
                            # reset the segment_dict
                            segment_dict = collections.OrderedDict()
                        close_segment = False

            elif (divider not in l) and header_line:
                # if we aren't dealing with a header_line
                # but header_line is true
                # Then this must be the title line for a segment
                # clean up the line by stripping extraneous characters
                l = l.rstrip()
                if len(l) <= 1:
                    # if the cleaned line is empty we will
                    # assume it is a Claim Summary
                    # Medicare Claims have a blank line between
                    # headers for the Claim Summary
                    l = "Claim Summary"
                # now compare l to a segment list for a match
                if find_segment(l):
                    # print("Segment list: %s FOUND" % l)
                    seg_returned = get_segment(l)
                    k = seg_returned["name"]
                    # print("k set to [%s]" % k)
                    current_segment, segment_dict = segment_prefill(seg_returned)
                    # print("Current_Segment: %s" % current_segment)
                    # print("segment_dict: %s" % segment_dict)
                else:
                    # We didn't find a match so let's set it to "Other"
                    current_segment = "other"
                    segment_dict = collections.OrderedDict()

            else:
                # We are dealing with a detail line so we need to process it
                # print("Line [%s: %s]" % (i,l))

                # Let's check for Source and set that up
                segment_source = set_source(segment_source, k, v)
                if k.upper() == "SOURCE":
                    k = k.lower()
                    v = segment_source

                if current_segment == "header":
                    # Now we deal with some special items.
                    # The Date and time in the header section
                    if k[2] == "/":
                        # print("got the date line")
                        v = {"value": parse_time(l)}
                        k = "effectiveTime"
                        close_segment = True

                # Build a string to use to find lower level seg entries
                drill_down = current_segment + "." + k
                update_name = translate_field(drill_down)
                if update_name == "":
                    k = k.lower().replace(" ", "_")
                else:
                    k = update_name

                # print("dd:%s:%s to %s" % (drill_down,update_name, k))
                # print("k:%s" % k)
                if k != seg_returned["name"]:
                    # check if the key = the section name
                    # If it does don't write key and value
                    print("Adding to generic/segment-k=v:%s=%s" % (k, v))
                    generic_dict[k] = v
                    segment_dict[k] = v

                if seg_returned['end_match'] in k:
                    # We found the last line in a segment
                    print("End Found: %s "
                          "is in %s" % (seg_returned['end_match'], k))
                    close_segment = True

                if close_segment:
                    # Update the source field in the segment
                    if current_segment != "header":
                        print("source: %s" % segment_source)
                        segment_dict["source"] = segment_source
                    # write the segment to items
                    print("writing %s" % current_segment)
                    items[current_segment] = segment_dict
                    segment_dict = collections.OrderedDict()
                    close_segment = False

    f.close()
    return items

# is_header (ie. the line doesn't have a ":")
# if is_header
#   Match header.upper() against segment.header.upper() entries
#       if matched
#          get segment.filetype (eg. CMS or VA)
#          get segment.prefill_content for segment
#          get segment.level (ie. header = 0)
#          get segment.name
#          get segment.key_match_end
#          get segment.prefix
# else
#   split line by ":" to key and val
#   Match segment.prefix.upper()+key.upper() against body.header.upper()
#       if matched
#          get body.filetype (eg. CMS or VA)
#          get body.prefill_content for key
#          get body.level (ie. level of dict embed)
#          get body.name
#          get body.key_match_end
#   Deal with special case content
#   eg. date inside header (key[2]="/")
#          reset key and val
#          format date
#   Match segment.prefix.upper()+key.upper() against field.name
#          reset key with field.name
#
#   write the generic_dict with [key]=val
#   write section[level]=generic_dict


def get_segment(title):

    result = {}

    for k in seg:
        if title in k["key"]:
            result = k
            break

    return result


def find_segment(title):

    result = False
    for k in seg:
        # print(k)
        if title in k["key"]:
            # print("Match: %s : %s" % (title, k['key']))
            result = True
            break
    return result


def parse_time(t):
    # convert time to  json format
    t = t.strip()
    time_value = datetime.strptime(t, "%m/%d/%Y %I:%M %p")
    # print(time_value)
    return_value = time_value.strftime("%Y%m%d%H%M%S+0500")
    # print(return_value)
    return return_value


def segment_prefill(seg):
    # Receive the Segment information for a header line
    # get the seg["prefill"] and iterate through the dict
    # assigning to segment_dict
    # First we reset the segment_dict as an OrderedDict
    segment_dict = collections.OrderedDict()
    current_segment = seg["name"]
    prefill = seg['prefill']
    # print(prefill)
    for pi, pv in prefill.items():
        # print(pi,":" ,pv)
        segment_dict[pi] = pv

    return current_segment, segment_dict


def segment_eval(input_line):
    # check for section and load in any pre-defined values to the dict
    segment_dict = collections.OrderedDict()
    if input_line == "MYMEDICARE.GOV PERSONAL HEALTH INFORMATION":
        current_segment = "header"
        segment_dict["title"] = input_line
        segment_dict["languageCode"] = "code=\"en-US\""
        segment_dict["versionNumber"] = {"value": "3"}
        segment_dict["effectiveTime"] = {}
        segment_dict["confidentialityCode"] = {"code": "N",
                                               "codeSystem": "2.16.840.1."
                                                             "113883.5.25"}
        segment_dict["originator"] = "MyMedicare.gov"
    else:
        current_segment = input_line

    return current_segment, segment_dict


def set_source(current_source, key, value):
    # Set the source of the data

    if key.upper() == "SOURCE":
        result = ""
        # print("Found Source: [%s:%s]" % (key,value))
        if value.upper() == "SELF-ENTERED":
            result = "patient"
        elif value.upper() == "MYMEDICARE.GOV":
            result = "MyMedicare.gov"
        else:
            result = value.upper()
        # print("[%s]" % result)
        return result
    else:
        return current_source


def translate_field(fld):
    # lookup field and return new field
    result = ""
    # print("FLD:%s" % fld)
    for ky, vl in enumerate(FLD_TRANSLATE):
        # print("k/v: %s/%s" % (ky, vl))
        # print("vl:%s, %s" % (vl['input'],vl['output']))
        if vl['input'] == fld:
            result = vl['output']
            # print("Field: %s:%s" % (fld,result))
            break
    return result


def build_bp_readings(items):

    bpdictlist = []
    i = 0
    for it in items:
        if "Measurement Type" in it:
            if it['Measurement Type'] == "Blood pressure":
                """The next 4 lines are date time systolic and diastolic"""
                bpdict = {}
                bpdict.update(items[i + 1])
                bpdict.update(items[i + 2])
                bpdict['bp'] = "bp=%s/%s" % (items[i + 3]['Systolic'],
                                             items[i + 4]['Diastolic'])
                bpdict['bp_sys'] = items[i + 3]['Systolic']
                bpdict['bp_dia'] = items[i + 4]['Diastolic']
                bpdictlist.append(bpdict)
        i += 1
    return bpdictlist


def build_wt_readings(items):

    wtdictlist = []
    i = 0
    for it in items:
        if "Measurement Type" in it:
            if it['Measurement Type'] == "Body weight":
                """The next 4 lines are date time systolic and diastolic"""
                wtdict = {}
                wtdict.update(items[i + 1])
                wtdict.update(items[i + 2])
                wtdict['wt'] = "wt=%sl" % (items[i + 3]['Body Weight'])
                wtdictlist.append(wtdict)
        i += 1
    return wtdictlist


def build_mds_readings(items):
    # print("here- build mds readings")
    mdsdictlist = []
    i = 0
    for it in items:
        if "Medication" in it:
            mdsdict = {}
            mdsdict.update(items[i])
            j = 0
            while 'Prescription Number' not in items[i + j]:
                # print(items[i + j])
                j += 1
                mdsdict.update(items[i + j])
                mdsdictlist.append(mdsdict)
        i += 1
    return mdsdictlist


def build_simple_demographics_readings(items):
    fnfound = False
    lnfound = False
    mifound = False
    gfound = False
    dobfound = False

    demodict = {}
    for it in items:
        if "First Name" in it and fnfound is False:
            demodict['first_name'] = it['First Name']
            fnfound = True

        if "Middle Initial" in it and mifound is False:
            demodict['middle_initial'] = it['Middle Initial']
            mifound = True

        if "Last Name" in it and lnfound is False:
            demodict['last_name'] = it['Last Name']
            lnfound = True

        if "Gender" in it and gfound is False:
            g = it['Gender'].split(" ")
            demodict['gender'] = g[0]
            gfound = True

        if "Date of Birth" in it and dobfound is False:
            (m, d, y) = it['Date of Birth'].split("/")
            demodict['date_of_birth'] = it['Date of Birth']
            dob = date(int(y), int(m), int(d))
            # today = date.today()
            demodict['num_age'] = age(dob)
            dobfound = True

    return demodict


def tojson(items):
    """tojson"""
    itemsjson = json.dumps(items, indent=4)
    return itemsjson


def write_file(write_dict, Outfile):
    f = open(Outfile, 'w')
    f.write(tojson(write_dict))
    f.close()
