"""
python-bluebutton
FILE: cms_custom
Created: 3/26/15 9:39 AM

Custom processing of sections of the CMS Blue Button text file
__author__ = 'Mark Scrimshire:@ekivemark'

"""
import logging

from collections import OrderedDict

from apps.cmsblue.cms_parser_utilities import *

logger = logging.getLogger('hhs_server.%s' % __name__)


def custom_family_history(strt_ln,
                          ln_control,
                          match_ln,
                          strt_lvl,
                          ln_list,
                          seg,
                          seg_name):
    # Custom processing for Family History section
    # Needed due to multiple uses of "Type" at same level in segment

    # Input:
    # strt_ln = current line number in the dict
    # ln_control = entry from SEG_DEF for the start_ln
    # match_ln = list array to build a breadcrumb match setting
    # eg. emergencyContact.name.address
    # start_lvl = current level for record. top level = 0
    # ln_list = the dict of lines to process
    # { "0": {
    #        "line": "MYMEDICARE.GOV PERSONAL HEALTH INFORMATION",
    #        "type": "HEADER",
    #        "key": 0,
    #        "level": 0
    #    }
    # },
    # seg = dict returned from process_header
    # seg_name = dict key in seg returned from process_header

    current_segment = seg_name
    # seg_type = check_type(seg[seg_name])
    end_segment = False
    wrk_ln = strt_ln

    wrk_seg_def = {}

    # ln_control_alt = ln_control

    # wrk_ln_head = False

    kvs = {"k": "",
           "v": "",
           "source": "",
           "comments": [],
           "claimNumber": "",
           "ln": 0,
           "category": ""}

    # wrk_segment = seg_name
    # multi = key_is("multi", ln_control, "TRUE")

    save_to = seg[seg_name]
    # logger.debug("pre-load the data passed in to ", seg_type,
    #              "<<<<<<<<<<<<<<<<",
    #              "seg[" + seg_name + "]:", to_json(seg[seg_name]))

    process_dict = OrderedDict()
    process_list = []

    # get current line
    current_line = get_line_dict(ln_list, wrk_ln)
    wrk_ln_lvl = current_line["level"]

    # Update match_ln with headers name from SEG_DEF (ie. ln_control)
    match_ln = update_match(strt_lvl, seg_name, match_ln)

    match_hdr = combined_match(wrk_ln_lvl, match_ln)
    # Find segment using combined header

    type_count = 0

    # logger.debug(">>==>>==>>==>>==>>==>>==>>==>>==>>==>>==>>",
    #              "type:", seg_type,
    #              "seg:", seg,
    #              "seg_name:", seg_name,
    #              "ln_control:", to_json(ln_control),
    #              "strt_lvl:", strt_lvl,
    #              "match_ln:", match_ln,
    #              "current_line:", current_line,
    #              ">>==>>==>>==>>==>>==>>==>>==>>==>>==>>==>>")

    #############################################################
    #############################################################
    # START OF WHILE LOOP
    #############################################################
    while not end_segment and (wrk_ln <= len(ln_list) - 1):
        if wrk_ln == len(ln_list) - 1:
            end_segment = True

        # not at end of file or segment
        # Lookup SEG DEF Record

        wrk_ln_lvl = current_line["level"]
        match_ln = update_match(wrk_ln_lvl,
                                headlessCamel(current_line["line"]),
                                match_ln)
        match_hdr = combined_match(wrk_ln_lvl,
                                   match_ln)
        # Find segment using combined header

        is_line_seg_def = find_segment(match_hdr, True)
        # Find SEG_DEF with match exact = True

        if is_line_seg_def:
            wrk_seg_def = get_segment(match_hdr, True)
            # We found a SEG_DEF match with exact=True so Get the SEG_DEF

        kvs = assign_key_value(current_line,
                               wrk_seg_def,
                               kvs)

        # process items unless we hit the 2nd k == "type"
        if kvs["k"].upper() == "TYPE" and type_count == 0:
            type_count += 1

        elif kvs["k"].upper() == "TYPE" and type_count == 1:
            # loop through lines until we get to next family member
            # or end of segment
            wrk_ln, kvs = write_conditions(wrk_ln,
                                           kvs,
                                           wrk_seg_def,
                                           ln_list)
            # reset type_count
            type_count = 0

        if kvs["k"] in process_dict:
            # repeated item so clean up current dict
            # write source and comments
            process_dict = write_source(kvs, process_dict)
            # then add to process_list
            process_list.append(process_dict)
            # then clear down process_dict
            process_dict = OrderedDict({kvs["k"]: kvs["v"]})

        # add line to dict

        process_dict[kvs["k"]] = kvs["v"]

        # if key_is_in("dict_name", wrk_seg_def):
        #     process_dict[wrk_seg_def["dict_name"]] = (kvs["k"], kvs["v"])
        # else:
        #     process_dict.update({kvs["k"]: kvs["v"]})

        # end of line assignment

        # logger.debug("Current_line:", current_line,
        #              "match_ln:", match_ln,
        #              "kvs:", kvs,
        #              "process_dict", process_dict,
        #              "is_line_seg_def:", is_line_seg_def,
        #              "wrk_seg_def:", wrk_seg_def)

        # increment the counter
        wrk_ln += 1

        # update the current_line information
        current_line = get_line_dict(ln_list, wrk_ln)

        if current_line["type"] == "HEADER":
            # We found the next header
            wrk_ln -= 1
            end_segment = True
            # logger.debug("Found next section!!!!!!!!")

    # end of While not end_segment and (wrk_ln <= len(ln_list)-1):

    #############################################################
    # END OF WHILE LOOP
    #############################################################
    #############################################################
    end_ln = wrk_ln

    if key_is("type", ln_control, "LIST"):
        # print("-------------------------")
        if len(process_dict) > 0:
            # print("adding dict to list")
            # print("")
            if not key_is_in("source", process_dict):
                # print("adding source", kvs["source"])
                process_dict["source"] = kvs["source"]
            process_list.append(process_dict)
        # print("seg:", seg)
        # print("adding from process_list")
        if check_type(seg[seg_name]) == "LIST":
            seg[seg_name].append(process_list)

        # print(seg[seg_name])
    elif key_is("type", ln_control, "DICT"):
        # print("adding from process_dict")
        seg[seg_name] = process_dict
    # logger.debug("<<==<<==<<==<<==<<==<<==<<==<<==<<",
    #              "returning end_ln:", end_ln,
    #              "wrk_ln:", wrk_ln,
    #              "end_segment:", end_segment,
    #              "wrk_segment:", wrk_segment,
    #              "type:", wrk_seg_def,
    #              "ln_control[type]:", to_json(ln_control),
    #              "returning dict(current_line):", to_json(seg),
    #              "from process_dict:", to_json(process_dict),
    #              "from process_list:", process_list,
    #              "<<==<<==<<==<<==<<==<<==<<==<<==<<")
    if len(save_to) == 1:
        save_to = seg[seg_name]
        # print ("seg:", seg)

    return end_ln, save_to, current_segment


def write_conditions(wrk_ln, kvs, wrk_seg_def, ln_list):
    # loop through lines until:
    # line type=header

    current_line = get_line_dict(ln_list, wrk_ln)
    sub_kvs = {"k": "",
               "v": "",
               "source": "",
               "comments": [],
               "claimNumber": "",
               "ln": 0,
               "category": ""}
    for k, v in kvs.items():
        sub_kvs[k] = v

    sub_kvs = assign_key_value(current_line, wrk_seg_def, sub_kvs)

    loop_more = True
    # ln_type = current_line["type"]
    not_eol = not (is_eol(wrk_ln, ln_list))

    kvs["k"] = "condition"
    kvs["v"] = []

    process_dict = OrderedDict()

    # logger.debug("not eol:", not_eol,
    #              "current_line:", current_line,
    #              "kvs:", kvs,
    #              "sub_kvs:", sub_kvs)

    while loop_more and not_eol and is_body(current_line):
        # break out of loop on following conditions:
        # End of list
        # End of segment ie. Line Type = HEADER
        # Reached the next Family Member sub-section

        # We come in with sub_kvs set

        if sub_kvs["k"] in process_dict:
            # logger.debug("process_dict:", process_dict,
            #              "sub_kvs:", sub_kvs,
            #              "kvs:", kvs)
            process_dict = write_source(sub_kvs, process_dict)
            kvs["v"].append(process_dict)
            process_dict = OrderedDict()

        process_dict[sub_kvs["k"]] = sub_kvs["k"]

        # Increment the line
        wrk_ln += 1
        current_line = get_line_dict(ln_list, wrk_ln)
        sub_kvs = assign_key_value(current_line, wrk_seg_def, sub_kvs)

        if sub_kvs["k"].upper() == "FAMILYMEMBER":
            # drop from loop
            loop_more = False
        else:
            # Move to the next line
            not_eol = not (is_eol(wrk_ln, ln_list))

    # end while not end_segment

    # logger.debug("END OF WRITE_CONDITIONS",
    #              "wrk_ln:", wrk_ln,
    #              "kvs:", kvs,
    #              "sub_kvs:", sub_kvs,
    #              "process_dict:", process_dict)

    if len(process_dict) > 0:
        kvs["v"].append(process_dict)
    # step the line count back 1
    wrk_ln -= 1

    return wrk_ln, kvs
