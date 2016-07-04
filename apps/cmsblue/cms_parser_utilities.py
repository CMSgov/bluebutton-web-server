"""
python-bluebutton
FILE: cms_parser_utilities
Created: 3/9/15 5:34 PM

Takes CMS BlueButton v2.0 File and converts to JSON
This provides partial compatibility with full JSON/XML format
__author__ = 'Mark Scrimshire:@ekivemark'

"""
from datetime import datetime
from collections import OrderedDict

from apps.cmsblue.file_def_cms import SEG_DEF
from apps.cmsblue.usa_states import STATES

import logging
import re
import json
import inspect
import six

logger = logging.getLogger('hhs_server.%s' % __name__)


def process_header(strt_ln, ln_control, strt_lvl, ln_list):
    # Input:
    # strt_ln = current line number in the dict
    # ln_control = entry from SEG_DEF for the start_ln
    # match_ln = list array to build a breadcrumb match setting
    # eg. emergencyContact.name.address
    # start_lvl = current level for record. top level = 0
    # ln_list = the dict of lines to process
    # { "0": {
    # "line": "MYMEDICARE.GOV PERSONAL HEALTH INFORMATION",
    #        "type": "HEADER",
    #        "key": 0,
    #        "level": 0
    #    }
    # },

    # unused = strt_lvl
    wrk_add_dict = OrderedDict()

    # Setup
    # we dropped in to this function because we found a SEG_DEF dict
    # which was loaded in to ln_control.

    segment = ln_control["name"]

    wrk_ln_dict = get_line_dict(ln_list, strt_ln)
    # Load wrk_ln_dict ready for evaluating line in setup_header

    wrk_add_dict = setup_header(ln_control, wrk_ln_dict)
    # ln_ctrl = SEG_DEF entry
    # wrk_ln_dict is the current line from ln_list[strt_ln]

    return strt_ln, wrk_add_dict, segment


def process_subseg(strt_ln,
                   ln_control,
                   match_ln,
                   strt_lvl,
                   ln_list,
                   seg,
                   seg_name):
    # Input:
    # strt_ln = current line number in the dict
    # ln_control = entry from SEG_DEF for the start_ln
    # match_ln = list array to build a breadcrumb match setting
    # eg. emergencyContact.name.address
    # start_lvl = current level for record. top level = 0
    # ln_list = the dict of lines to process
    # { "0": {
    # "line": "MYMEDICARE.GOV PERSONAL HEALTH INFORMATION",
    #        "type": "HEADER",
    #        "key": 0,
    #        "level": 0
    #    }
    # },
    # seg = dict returned from process_header
    # seg_name = dict key in seg returned from process_header

    # FIXED: email address not written in patient section
    # FIXED: Write phones as dict in patient section
    # FIXED: medicalConditions - 2nd items is skipped
    # FIXED: Double comment lines written in allergies sections
    # FIXED: Allergies section is empty
    # FIXED: Medications - last entry does not get source info

    # FIXED: Fix Funky errors [Family History] - some entries not written
    # FIXED: Preventive Services - Some items not added
    # FIXED: Providers - last entry does not get source info
    # FIXED: Providers - Fields not in order
    # FIXED: Pharmacies - Last record missing Pharmacy Name
    # FIXED: Pharmacies - last entry does not get source info
    # FIXED: missing "category": "Medicare" fixed with "Pre" definition

    # FIXED: category dict written after insurance section
    # FIXED: Employer Subsidy Header not written
    # FIXED: Primary Insurance Header not written
    # FIXED: Other Insurance Header not written

    # FIXED: Claim Details need to be embedded inside Claim Header
    # FIXED: Write Claim details as list of dicts with new dict on repeat of
    #       line number
    # FIXED: Multiple Claims Headers and Details not handled
    # FIXED: Claims - First Header and Last Claim Detail written
    # FIXED: Fix Time fields (minutes dropped after colon)

    # FIXED: Last Claim Header is appended to previous claim line
    # FIXED: Last Claim number section does not get sub-listed inside
    # claim header section (probably due to bug in claim header)

    # FIXED: comments in header are dropped. Change Assign_key_value()
    # FIXED: Time in header is not written
    # FIXED: Removed "/" from field names (kvs["k"]) in
    #        assign_key_values()

    # FIXED: Contact Name sections written differently between first
    #        and subsequent sections

    # FIXED: Insurance
    # FIXED: Insurance section employer subsidy not writing multiple plans
    # FIXED: planType from medicare section is written as category
    # FIXED: Employer Subsidy is not written as sub-category
    # FIXED: Category does not get replicated to each sub-item
    # FIXED: First category item in each insurance section is blank
    # FIXED: Only last Employer Subsidy entry is written
    # FIXED: Only last Other Insurance entry is written
    # FIXED: By changing SEG_DEF sections to type of "list"

    # FIXED: Claims
    # FIXED: "claim": [] written to claim header after first claim
    # FIXED: "details": [] written to first claim line details section

    # FIXED: Part D Claims are not written due to different format
    # FIXED: "type": Part D and no Claim Header

    # FIXED: Last line in file was not being written

    # The claims section of the CMS BlueButton file appears to have an
    # issue. The Claim Headers are not titled there is only the two
    # dashed lines BUT the last claim header does not get preceded by
    # the dashed lines. So there is nothing to indicate a new claim.

    # Therefore implement a fix that since the claims come at the end
    # of the file we will assign a claim number field in to the line dict
    # we create and increment that on change of "Line Number" found in
    # the lines

    current_segment = seg_name
    # seg_type = check_type(seg[seg_name])
    end_segment = False
    wrk_ln = strt_ln

    wrk_seg_def = {}

    ln_control_alt = ln_control

    wrk_ln_head = False
    kvs = {"k": "",
           "v": "",
           "source": "",
           "comments": [],
           "claimNumber": "",
           "ln": 0,
           "category": ""}
    wrk_segment = seg_name
    multi = key_is("multi", ln_control, "TRUE")

    # save_to = seg[seg_name]
    # Disable pre-writing of save_to and add to process_dict instead
    save_to = {}

    # logger.debug("pre-load data passed to " + seg_type + " <<<<<<<<<<<<<<<",
    #              "seg[" + seg_name + "]:",
    #              to_json(seg[seg_name]))

    proc_dict = OrderedDict(seg[seg_name])
    proc_list = []

    # get current line
    current_line = get_line_dict(ln_list, wrk_ln)
    wrk_ln_lvl = current_line["level"]

    # Update match_ln with headers name from SEG_DEF (ie. ln_control)
    match_ln = update_match(strt_lvl, seg_name, match_ln)

    match_hdr = combined_match(wrk_ln_lvl, match_ln)
    # Find segment using combined header

    # logger.debug(">>==>>==>>==>>==>>==>>==>>==>>==>>==>>==>>",
    #              "type:", seg_type,
    #              "seg", to_json(seg),
    #              "seg_name:", seg_name,
    #              "ln_control:", to_json(ln_control),
    #              "wrk_ln:", wrk_ln,
    #              "strt_lvl:", strt_lvl,
    #              "match_ln:", match_ln,
    #              ">>==>>==>>==>>==>>==>>==>>==>>==>>==>>==>>")

    while not end_segment and (wrk_ln <= len(ln_list)):
        if wrk_ln == len(ln_list):  # - 1:
            end_segment = True

        # not at end of file

        # logger.debug(">>>>>TOP of while loop",
        #              "wrk_ln:", wrk_ln,
        #              "current_line:", to_json(current_line),
        #              "match_ln:", match_ln,
        #              "process_dict:", proc_dict,
        #              # "process_list:", proc_list,
        #              )

        # update the match string in match_ln

        is_line_seg_def = find_segment(match_hdr, True)
        # Find SEG_DEF with match exact = True

        # logger.debug("*****************PRESET for line***********",
        #              "wrk_ln_lvl:", wrk_ln_lvl,
        #              "match_ln:", match_ln,
        #              "match_hdr:", match_hdr,
        #              "is_line_seg_def:", is_line_seg_def,
        #              "wrk_seg_def:", wrk_seg_def)

        if is_line_seg_def:
            # We found an entry in SEG_DEF using match_hdr

            wrk_seg_def = get_segment(match_hdr, True)
            # We found a SEG_DEF match with exact=True so Get the SEG_DEF

            match_ln = update_match(wrk_ln_lvl, wrk_seg_def["name"],
                                    match_ln)
            # update the name in the match_ln dict

            # we also need to check the lvl assigned to the line from
            # SEG_DEF
            wrk_ln_lvl = wrk_seg_def["level"]
            multi = key_is("multi", wrk_seg_def, "TRUE")

            # logger.debug("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            #              "is_line_seg_def:", is_line_seg_def,
            #              "wrk-seg_def:", to_json(wrk_seg_def),
            #              "match_ln:", match_ln,
            #              "wrk_ln:", wrk_ln,
            #              "strt_ln:", strt_ln,
            #              "current_line type:",
            #              current_line["type"])

            if (wrk_ln != strt_ln) and (is_head(current_line)):
                # we found a new header
                # We have to deal with claims lines and claims headers
                # within claims. They have a different level value
                # So test for level = strt_lvl
                # logger.debug("DEALING WITH NEW HEADER:%s" %
                #              current_line["line"])

                # set wrk_ln_head = True
                # Clean up the last section since we are in a
                # new header
                proc_dict, proc_list, = write_proc_dl(kvs,
                                                      proc_dict,
                                                      proc_list)

                # Now clear down the dict and
                # add the new item

                proc_dict = OrderedDict()

                wrk_segment, proc_dict = segment_prefill(wrk_seg_def,
                                                         proc_dict)

                # new fix end
                wrk_ln_head = True
                wrk_ln_lvl = get_level(wrk_seg_def)

                # logger.debug("RECURSIVE CALL",
                #              "wrk_ln:", wrk_ln,
                #              "wrk_seg_def:", wrk_seg_def,
                #              "match_ln:", match_ln,
                #              "wrk_ln_lvl:", wrk_ln_lvl,
                #              # "process_list:", proc_list,
                #              "process_dict:", proc_dict,
                #              "seg:", seg,
                #              "seg_name:", seg_name)

        else:
            # NOT is-line-seg_def
            # logger.debug("--------------------------------",
            #              "wrk_ln:", wrk_ln,
            #              "wrk_ln_head:", wrk_ln_head,
            #              "wrk_seg_def:", wrk_seg_def,
            #              "updating wrk_seg_def",
            #              "ln_control_alt:", ln_control_alt,
            #              "SETTING to ln_control_alt")
            if not ln_control_alt == {}:
                wrk_seg_def = ln_control_alt
            else:
                wrk_seg_def = ln_control

        # Get key and value
        kvs = assign_key_value(current_line,
                               wrk_seg_def,
                               kvs)

        # logger.debug("wrk_ln_lvl:", wrk_ln_lvl, "match_hdr:", match_hdr,
        #              "kvs:", kvs,
        #              "Multi:", multi,
        #              "is_line_seg_def:", is_line_seg_def,
        #              "process_dict:", proc_dict,
        #              # "process_list:", proc_list,
        #              "end_segment:", end_segment,
        #              "wrk_ln_head:", wrk_ln_head)

        # Update kvs to dict or list
        if not end_segment:
            # We need to process the line

            # assign "pre" values from SEG_DEF
            # to work_add_dict
            # logger.debug("WRK_LN_HEAD:", wrk_ln_head,
            #              "wrk_seg_def:", wrk_seg_def,
            #              "process_dict:", proc_dict,
            #              # "process_list:", proc_list,
            #              )

            if wrk_ln_head:
                # Post the dict to a list and clear down
                # before writing pre-fill
                # check for source and write it to proc_dict

                # Move to sub-function()

                proc_dict, proc_list, = write_proc_dl(kvs,
                                                      proc_dict,
                                                      proc_list)

                # Replace code with sub-function()

                # Now clear down the dict and
                # add the new item

                proc_dict = OrderedDict()

                wrk_segment, proc_dict = segment_prefill(wrk_seg_def,
                                                         proc_dict)

                # logger.debug("Just ran segment_pre-fill:", wrk_ln_head,
                #              "wrk_segment:", wrk_segment,
                #              "process_dict:", proc_dict,
                #              # "process_list:", proc_list,
                #              )

            else:  # NOT wrk_ln_head
                # logger.debug("wrk_ln_head:", wrk_ln_head,
                #              "process_dict:", proc_dict,
                #              # "PROCESS_LIST:", proc_list,
                #              )
                pass

            # Do we need to override the key using field or name
            # from SEG_DEF?

            # pass in match_ln, match_hdr, and wrk_lvl to allow
            # Override to be checked

            if "SOURCE" in kvs["k"].upper():
                # source was saved in the assign step.
                # we don't write it out now. instead save it till a block
                # is written
                pass

            # Now we check if we are dealing with an address block
            if ("ADDRESSLINE1" in kvs["k"].upper()) or \
                    ("ADDRESSTYPE" in kvs["k"].upper()):
                # Build an Address Block
                # By reading the next lines
                # until we find "ZIP"
                # return Address dict and work_ln reached

                kvs["v"], wrk_ln = build_address(ln_list, wrk_ln)
                kvs["k"] = "address"
                # logger.debug("Built Address wrk_ln now:",
                #              wrk_ln,
                #              "k:",
                #              kvs["k"],
                #              "v:",
                #              kvs["v"])

            if "COMMENTS" in kvs["k"].upper() and not wrk_ln_head:
                # print "We found a comment", kvs["k"],":", kvs["v"]
                # and we are NOT dealing with a header
                # if value is assigned to comments we need to check
                # if comments already present
                # if so, add to the list

                proc_dict = write_comment(proc_dict, kvs)

                # logger.debug("is_line_seg_def:", is_line_seg_def,
                #              "wrk_seg_def", wrk_seg_def,
                #              "wrk_ln:", wrk_ln,
                #              "kvs:", kvs,
                #              "current_line:", current_line,
                #              "process_dict:", proc_dict)

            if multi:
                # logger.debug("******************************",
                #              "MULTI:", multi)
                if key_is("type", wrk_seg_def, "LIST"):
                    if key_is("sub_type", wrk_seg_def, "DICT"):
                        # logger.debug("LIST and sub_type: DICT",
                        #              "current_line:", current_line,
                        #              "process_dict:", proc_dict,
                        #              # "process_list:", proc_list,
                        #              "kvs:", kvs)
                        if kvs["k"] in proc_dict:
                            # logger.debug("k:", kvs["k"],
                            #              "in:", proc_dict)

                            proc_dict, proc_list = write_proc_dl(kvs,
                                                                 proc_dict,
                                                                 proc_list)
                            # Now clear down the dict and
                            # add the new item

                            proc_dict = OrderedDict()

                            if not kvs["k"].upper() == "COMMENTS":
                                # print "skipping comments"
                                proc_dict[kvs["k"]] = kvs["v"]
                            # print "proc_dict (after write):", \
                            #    proc_dict
                        else:
                            if not kvs["k"].upper() in ["CATEGORY",
                                                        "SOURCE"]:
                                proc_dict[kvs["k"]] = kvs["v"]
                                # logger.debug("After " + kvs["k"] +
                                #              " not found",
                                #              "in process_dict:",
                                #              proc_dict,
                                #              "SO IT WAS ADDED -" +
                                #              " if not CATEGORY")
                    else:
                        if key_is_in("sub_type", wrk_seg_def):
                            # logger.debug("wrk_seg_def sub_type:",
                            #              wrk_seg_def["sub_type"])
                            pass

                        proc_dict[kvs["k"]] = [kvs["v"]]
                        # print("proc_dict:", proc_dict)
                        # TESTING disabling save_to write
                        # save_to = write_save_to(save_to, proc_dict)

                elif key_is("type", wrk_seg_def, "DICT"):
                    # print("wrk-seg_def:", wrk_seg_def)
                    if key_is("sub_type", wrk_seg_def, "DICT"):
                        # logger.debug("DICT and sub_type: DICT",
                        #              "write " + wrk_seg_def["name"] + ":",
                        #              kvs["v"],
                        #              "ln_control:", to_json(ln_control),
                        #              "wrk_seg_def:", to_json(wrk_seg_def),
                        #              "current_line:", to_json(current_line),
                        #              "process_dict:", to_json(proc_dict),
                        #              # "process_list:", proc_list,
                        #              "kvs:", kvs)

                        # Write what
                        if not kvs["k"].upper() == "SOURCE":
                            # proc_dict[wrk_seg_def["name"]] = kvs["v"]
                            proc_dict[kvs["k"]] = kvs["v"]
                        # logger.debug("just wrote non-source line",
                        #              "process_dict:", proc_dict)

                    else:
                        # logger.debug("No sub_type")
                        if key_is_in("sub_type", wrk_seg_def):
                            # logger.debug("type: DICT and sub_type:%s" %
                            #              wrk_seg_def["sub_type"])
                            pass
                        else:
                            # logger.debug("writing to proc_dict:%s" %
                            #              proc_dict)

                            # type: dict
                            # dict_name: phone
                            # field : home
                            # k: homePhone v = ""
                            # needs to get written as
                            # phone {"home": "", "work": "", "mobile": ""}
                            # proc_dict[wrk_seg_def["dict_name"]] =
                            #               {wrk_seg_def["field"]: kvs["v"]
                            # follow on elements need to check:
                            # wrk_seg_def["dict_name"] or kvs["k"]

                            if key_is_in_subdict(kvs["k"], proc_dict):
                                # write the source first
                                # logger.debug("roll a new process_dict")
                                proc_dict = write_source(kvs,
                                                         proc_dict)
                                # Append to the list
                                proc_list.append(proc_dict)
                                # Now clear down the dict and
                                # add the new item
                                proc_dict = OrderedDict()
                                proc_dict[kvs["k"]] = kvs["v"]

                            # logger.debug("didn't find:%s \nis_"
                            #              "line_seg_def:%s" % (kvs["k"],
                            #                                   is_line_seg_def))

                            if is_line_seg_def and key_is_in("dict_name",
                                                             wrk_seg_def):
                                # logger.debug("got dict_name:",
                                #              wrk_seg_def["dict_name"])
                                if not key_is_in(wrk_seg_def["dict_name"],
                                                 proc_dict):
                                    # logger.debug("no dict_name")
                                    if wrk_seg_def["dict_name"] == wrk_seg_def["name"]:
                                        # fix to write "contactName"
                                        # sections consistently
                                        proc_dict[wrk_seg_def["dict_name"]] = kvs["v"]
                                    else:
                                        proc_dict[wrk_seg_def["dict_name"]] = {wrk_seg_def["name"]: kvs["v"]}
                                    # process_dict[kvs["k"]] = kvs["v"]
                                else:
                                    # logger.debug("updating proc_dict:"
                                    #              "%s\nwith kvs:"
                                    #              "%s" % (proc_dict, kvs))
                                    # proc_dict[wrk_seg_def
                                    # ["dict_name"]] =kvs["v"]
                                    if check_type(proc_dict[wrk_seg_def["dict_name"]]) == "DICT":
                                        proc_dict[wrk_seg_def["dict_name"]].update({wrk_seg_def["name"]: kvs["v"]})
                                    else:
                                        proc_dict[wrk_seg_def["dict_name"]] = kvs["v"]
                            else:
                                # logger.debug("didn't get dict_name:%s" % kvs)
                                # proc_dict[kvs["k"]] = kvs["v"]

                                # ## TESTING disabling SAVE_TO
                                # save_to[kvs["k"]] = kvs["v"]
                                proc_dict.update({kvs["k"]: kvs["v"]})
                                # logger.debug("proc_dict updated to:%s" %
                                #              proc_dict)

                else:
                    if key_is_in("type", wrk_seg_def):
                        # logger.debug("wrk-seg_def - Type is:",
                        #              wrk_seg_def["type"],
                        #              "KVS:", kvs)
                        pass

            else:  # not multi
                if key_is("type", wrk_seg_def, "DICT"):

                    # logger.debug("Multi:", multi, " and type: DICT")

                    if kvs["k"].upper() == "COMMENTS" and \
                            key_is_in("comments",
                                      proc_dict):
                        pass
                    else:
                        if not is_line_seg_def:
                            # We have no special processing rules for
                            # this line
                            # logger.debug("is_line_seg_def: %s"
                            #              "\nkvs:%s" % (is_line_seg_def, kvs))
                            proc_dict[kvs["k"]] = kvs["v"]
                            # save_to[kvs["k"]] = kvs["v"]

                        elif key_is_in("dict_name", wrk_seg_def):
                            # logger.debug("processing:",
                            #              wrk_seg_def["dict_name"],
                            #              "kvs:", kvs,
                            #              "process_dict:", proc_dict)
                            if key_is_in(wrk_seg_def["dict_name"],
                                         proc_dict):
                                proc_dict[
                                    wrk_seg_def["dict_name"]].update(
                                    {kvs["k"]: kvs["v"]})
                            else:
                                # logger.debug("wrk_seg_def:", wrk_seg_def,
                                #              "kvs:", kvs)
                                proc_dict[wrk_seg_def["dict_name"]] = \
                                    OrderedDict({kvs["k"]: kvs["v"]})
                        else:
                            proc_dict[kvs["k"]] = kvs["v"]

                elif key_is("type", wrk_seg_def, "LIST"):
                    # logger.debug("Multi:%s and type: LIST\n"
                    #              "\nproc_dict:%s" % (multi,
                    #                                  to_json(proc_dict)))
                    proc_dict = update_save_to(proc_dict, kvs,
                                               kvs["k"], "v")
                    # save_to.extend([kvs["k"],kvs["v"]])

                # logger.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                #              "WHAT GETS WRITTEN HERE?",
                #              "MULTI:", multi,
                #              "kvs:", kvs,
                #              "ln_control:", to_json(ln_control),
                #              "wrk_seg_def:", to_json(wrk_seg_def),
                #              "current_line:", to_json(current_line),
                #              "proc_dict:", to_json(proc_dict),
                #              # "proc_list:", proc_list,
                #              "save_to:", to_json(save_to))

        wrk_ln_head = False
        # reset the Header indicator
        wrk_ln += 1
        # increment the line counter
        if wrk_ln < len(ln_list):   # - 1:
            current_line = get_line_dict(ln_list, wrk_ln)
            wrk_ln_lvl = current_line["level"]
            # update the match string in match_ln
            if find_segment(headlessCamel(current_line["line"]),
                            exact=True):
                wrk_seg_def = get_segment(
                    headlessCamel(current_line["line"]), exact=True)
                wrk_ln_lvl = max(current_line["level"],
                                 wrk_seg_def["level"])

            match_ln = update_match(wrk_ln_lvl,
                                    headlessCamel(current_line["line"]),
                                    match_ln)
            match_hdr = combined_match(wrk_ln_lvl, match_ln)
            # Find segment using combined header
            wrk_seg_def = get_segment(match_hdr, True)
            if is_head(current_line):
                ln_control_alt = wrk_seg_def
            # We found a SEG_DEF match with exact=True so Get the SEG_DEF

            if is_head(current_line) and (wrk_ln_lvl == strt_lvl):
                end_segment = True
            # logger.debug("current_line-head: %s\ncurrent_line:%s"
            #              "\nwrk_seg_def:%s\nmatch_hdr:%s"
            #              "\nmatch_ln:%s\nnwrk_ln_lvl:%s"
            #              "\nproc_dict:%s\n"
            #              "end_segment:%s" %  (is_head(current_line),
            #                                   current_line,
            #                                   wrk_seg_def,
            #                                   match_hdr,
            #                                   match_ln,
            #                                   wrk_ln_lvl,
            #                                   proc_dict,
            #                                   end_segment))
    # end while loop

    end_ln = wrk_ln - 1

    if key_is("type", ln_control, "LIST"):
        # print("-------------------------")
        if len(proc_dict) > 0:
            ############################################
            # if there is something in proc_dict
            # we need to add to proc_list using
            # write_proc_dl
            # it will deal with source addition
            # etc.
            ############################################

            proc_dict, proc_list = write_proc_dl(kvs,
                                                 proc_dict,
                                                 proc_list)

        # logger.debug("seg: %s adding from proc_list" % seg)

        if check_type(seg[seg_name]) == "LIST":
            seg[seg_name].append(proc_list)

        # logger.debug("seg_name:%s" % seg_name)

    elif key_is("type", ln_control, "DICT"):
        seg[seg_name] = proc_dict
        # logger.debug("Type is DICT",
        #              "adding from proc_dict",
        #              "process_dict:", proc_dict,
        #              "seg_name:", seg_name)

    # logger.debug("returning end_ln:", end_ln,
    #              "wrk_ln:", wrk_ln,
    #              "end_segment:", end_segment,
    #              "wrk_segment:", wrk_segment,
    #              "type:", wrk_seg_def,
    #              "current_line:", current_line,
    #              # "ln_control[type]:", to_json(ln_control),
    #              # "returning dict(current_line):", to_json(seg),
    #              # "from proc_dict:", to_json(proc_dict),
    #              "len(save_to):", len(save_to))

    if len(save_to) <= 1:
        save_to = seg[seg_name]
        # logger.debug("seg:", seg,
        #              "save_to:", to_json(save_to))

    return end_ln, save_to, current_segment

###############################################################
###############################################################
###############################################################
###############################################################


def adjusted_level(lvl, match_ln):
    # lookup the level based on the max of source line lvl
    # and SEG_DEF matched level

    result = lvl
    if find_segment(combined_match(lvl, match_ln)):
        seg_info = get_segment(combined_match(lvl, match_ln))
        if key_is_in("level", seg_info):
            result = max(lvl, seg_info["level"])

    # logger.debug("Level(lvl): %s \nResult:%s"
    #              "\nUsing match_ln:%s" % (lvl, result, to_json(match_ln)))

    return result


def assign_key_value(line_dict, wrk_seg_def, kvs):
    # evaluate the line to get key and value

    full_line = line_dict["line"]
    kvs["ln"] = line_dict["key"]
    claim = line_dict["claimNumber"]

    if kvs["ln"] > 140 and kvs["ln"] < 199:
        # logger.debug("line_dict:%s kvs:%s" % (line_dict, kvs))
        pass

    line_source = full_line.split(":")
    if len(line_source) > 1:
        kvs["k"] = headlessCamel(line_source[0])
        kvs["v"] = line_source[1].lstrip()
        # lines with more than 1 : get truncated.
        # so lets make sure we ge the whole line
        kvs = get_rest_of_line(kvs, line_source)
        kvs["v"] = kvs["v"].rstrip()

    else:
        if line_dict["type"].upper() == "HEADER":
            kvs["k"] = wrk_seg_def["name"]
            kvs["v"] = full_line.rstrip()
            kvs["category"] = kvs["v"]
            if wrk_seg_def["type"] == "dict":
                kvs["v"] = {kvs["k"]: kvs["v"]}
            elif wrk_seg_def["type"] == "list":
                kvs["v"] = kvs["v"]
        else:
            # add to comments list
            if not kvs["comments"]:
                kvs["comments"] = [kvs["v"]]
            else:
                kvs["comments"].append(kvs["v"])
            kvs["k"] = "comments"
            kvs["v"] = full_line

    if "SOURCE" in kvs["k"].upper():
        kvs["k"] = headlessCamel(kvs["k"])
        kvs = set_source(kvs)

        # print("SET source:", kvs["source"])

    if len(kvs["k"]) > 2:
        if kvs["k"][2] == "/":
            # print("got the date line in the header")
            kvs["v"] = {"value": parse_time(full_line)}
            kvs["k"] = "effectiveTime"
            # segment[current_segment]= {k: v}

    if "DATE" in kvs["k"].upper():
        kvs["v"] = parse_date(kvs["v"])

    if "DOB" == kvs["k"].upper():
        kvs["v"] = parse_date(kvs["v"])

    if "DOD" == kvs["k"].upper():
        kvs["v"] = parse_date(kvs["v"])

    # remove "/" in field names
    if "/" in kvs["k"]:
        kvs["k"] = kvs["k"].replace("/", "")
    if "-" in kvs["k"]:
        kvs["k"] = kvs["k"].replace("-", "")

    if claim:
        kvs["claimNumber"] = claim

    if kvs["ln"] > 140 and kvs["ln"] < 199:
        # logger.debug("kvs:s" % kvs)
        pass

    return kvs


def assign_simple_key(line, kvs):
    # evaluate the line to get key and value
    # Used in cms_file_read to extract Claim Number: "value" and
    # add to Line_dict so it can be used in detailed processing to
    # identify change of claim number

    line_source = line.split(":")
    if len(line_source) > 1:
        kvs["k"] = headlessCamel(line_source[0])
        kvs["v"] = line_source[1].lstrip()
        # lines with more than 1 : get truncated.
        # so lets make sure we ge the whole line
        kvs = get_rest_of_line(kvs, line_source)
        kvs["v"] = kvs["v"].rstrip()

    return kvs


def build_address(ln_list, wk_ln):
    # Build address block
    # triggered because current line has
    # k.upper() == "ADDRESSLINE1" or "ADDRESSTYPE"
    # so read until k.upper() == "ZIP"
    # then return address block and work_ln reached

    addr_block = OrderedDict([("addressType", ""),
                              ("addressLine1", ""),
                              ("addressLine2", ""),
                              ("city", ""),
                              ("state", ""),
                              ("zip", "")])

    end_block = False
    while not end_block:

        ln_dict = get_line_dict(ln_list, wk_ln)
        l = ln_dict["line"]

        k, v = split_k_v(l)
        # print(wk_ln, ":", k)

        if k in addr_block:
            # look for key in address block
            addr_block[k] = v
            end_block = False
            wk_ln += 1
        else:
            end_block = True

    # Check the format of the address block
    # sometimes the city, state, zip is entered in the addressLine1/2

    if len(addr_block["city"] + addr_block["state"] + addr_block["zip"]) < 2:
        # logger.debug("Empty city, state, zip: "
        #              "%s" % len(addr_block["city"] +
        #                          addr_block["state"] +
        #                          addr_block["zip"]))

        patch_addr = (
            addr_block["addressLine1"] + " " + addr_block[
                "addressLine2"]).rstrip()

        if addr_block["zip"] == "":
            # if zip is empty check end of patch address for zip
            # if we have a zip+4 then the 5th character from end will be -
            if patch_addr[-5] == "-":
                # We have a Zip + 4
                # so get last 10 characters
                addr_block["zip"] = patch_addr[-10:]
                patch_addr = patch_addr[1:-11]

            elif patch_addr[-5:].isdigit():
                # are the last 5 characters digits?
                addr_block["zip"] = patch_addr[-5:]
                patch_addr = patch_addr[1:-6]

            else:
                # do nothing
                pass

            if addr_block["zip"] != "" and addr_block[
                    "state"] == "" and patch_addr[-3] == " ":
                # We did something with the zip
                # so now we can test for " {State_Code}" at end of
                # patch_addr
                # get two characters
                new_state = patch_addr[-3:].lstrip().upper()
                if new_state in STATES:
                    # We got a valid STATE ID
                    # so add it to address_block
                    addr_block["state"] = new_state
                    # then remove from patch_addr
                    patch_addr = patch_addr[1:-3]

            if len(patch_addr.rstrip()) > len(
                    addr_block["addrLine1"]):
                # The zip and state were in Address Line 2
                # so we will update addressLine2
                addr_ln2 = patch_addr[(len(addr_block["addrLine1"]) - 1):]
                addr_ln2.lstrip()
                addr_ln2.rstrip()
                addr_block["addrLine2"] = addr_ln2
            else:
                # the zip and state came from addressLine1
                addr_block["addrLine1"] = patch_addr.rstrip()

    # logger.debug("ADDRESS BLOCK---------\n%s"
    #              "\nwk_ln: %s" % (to_json(addr_block), wk_ln - 1))

    return addr_block, wk_ln - 1


def check_type(check_this):
    # Check_this and return type

    result = "UNKNOWN"

    if isinstance(check_this, dict):
        result = "DICT"
    elif isinstance(check_this, list):
        result = "LIST"
    elif isinstance(check_this, tuple):
        result = "TUPLE"
    elif isinstance(check_this, str):
        result = "STRING"
    elif isinstance(check_this, bool):
        result = "BOOL"
    elif isinstance(check_this, int):
        result = "INT"
    elif isinstance(check_this, float):
        result = "FLOAT"

    return result


def combined_match(lvl, match_ln):
    # Get a "." joined match string to use to search SEG_DEF
    # lvl = number to iterate up to
    # match_ln = list to iterate through
    # return the combined String as combined_header
    # eg. patient.partAEffectiveDate

    ctr = 0
    combined_header = ""
    # print(match_ln)

    # logger.debug("lvl: %s\nmatch_ln: %s"
    #              "\ncombined_header:%s" % (lvl, match_ln, combined_header))

    while ctr <= lvl:
        if ctr == 0:
            combined_header = match_ln[ctr]
        else:
            if match_ln[ctr] is None:
                pass
            else:
                combined_header = combined_header + "." + match_ln[ctr]

        ctr += 1

    # logger.debug("lvl: %s\nmatch_ln: %s"
    #              "\ncombined_header:%s" % (lvl, match_ln, combined_header))

    return combined_header


def dict_in_list(ln_control):
    # if SEG_DEF type = list and sub_type = "dict"
    # return true

    result = False
    if ln_control["type"].upper() == "LIST":
        if ln_control["sub_type"].upper() == "DICT":
            result = True

    # logger.debug("ln_control:%s"
    #              "\nresult: %s" % (to_json(ln_control), result))

    return result


def do_DBUG(*args, **kwargs):
    # basic debug printing function
    # if string ends in : then print without newline
    # so next value prints on the same line

    # inspect.stack()[1][3] = Function that called do_DBUG
    # inspect.stack()[1][2] = line number in calling function

    # print inspect.stack()
    print("####################################")
    print("In function:", inspect.stack()[1][3], "[",
          inspect.stack()[1][2], "]")
    # print(args)

    # print(six.string_types)
    for i in args:
        if isinstance(i, six.string_types):
            if len(i) > 1:
                if i[-1] == ":":
                    print(i,)
                else:
                    print(i)
            else:
                print(i)
        else:
            print(i)
    print("####################################")

    return


def find_segment(title, exact=False):

    result = False
    ky = ""

    # cycle through the seg dictionary to match against title
    for ky in SEG_DEF:
        if exact is False:
            if title in ky["match"]:
                result = True
                break
        else:
            if ky["match"] == title:
                result = True
                break

    # logger.debug("title: %s."
    #              "\nmatch exact:%s"
    #              "ky in SEG_DEF:%s"
    #              "\nresult:%s" %  (title, exact, ky, result))

    return result


def get_dict_name(wrk_seg_def):
    # Get dict_name from wrk_seg_def
    # If no "dict_name" then return "name"

    if key_is_in("dict_name", wrk_seg_def):
        dict_name = wrk_seg_def["dict_name"]
    else:
        key_is_in("name", wrk_seg_def)
        dict_name = wrk_seg_def["name"]

    # logger.debug("wrk_seg_def:%s. dict_name:%s" % (to_json(wrk_seg_def),
    #                                                dict_name))

    return dict_name


def get_level(ln):
    # Get level value from SEG_DEF Line

    result = None

    if key_is_in("level", ln):
        result = ln["level"]

    return result


def get_line_dict(ln, i):
    # Get the inner line dict from ln

    found_line = ln[i]
    extract_line = found_line[i]

    if extract_line == {}:
        return extract_line

    # fix for missing claim header line(s)
    if "claim number:" in extract_line["line"].lower():
        # we need to check the previous line which
        # should be "claimHeader". If it isn't we have a missing
        # header so change this line content type to "HEADER"
        prev_i = max(0, i - 1)
        prev_line = ln[prev_i][prev_i]

        # logger.debug("ln[%s]:%s/%s" % (str(prev_i), ln[prev_i], prev_line))
        if prev_line == {}:
            # logger.debug("Previous Line was empty:%s " % prev_i)
            pass
        elif prev_line["line"].upper() == "CLAIM HEADER" or \
                "SOURCE:" in prev_line["line"].upper():
            # logger.debug("We found claim Number with previous claimHeader")
            pass
        else:
            # logger.debug("MISSING PREVIOUS CLAIM HEADER",
            #              "Extract line:", extract_line,
            #              "Previous Line:", prev_line,
            #              "Changing TYPE")
            extract_line["type"] = "HEADER"

    return extract_line


def get_rest_of_line(kvs, line_source):
    # Lines with multiple colons get truncated
    # so we need to rebuild the full value entry
    # line_source was split on ":" so we need to ad those back

    line_value = line_source[1]
    piece = 2

    if len(line_source) > 2:

        while piece < len(line_source):
            # skip the first item it will be the field name

            line_value = line_value + ":" + line_source[piece]
            piece += 1

    # logger.debug("piece:", piece, "line_value:", line_value,
    #              "Line_Source:", line_source)

    kvs["v"] = line_value.lstrip()

    return kvs


def get_segment(title, exact=False):
    # get the SEG_DEF record using title in Match

    result = {}
    ky = ""

    # cycle through the seg dictionary to match against title
    for ky in SEG_DEF:
        if not exact:
            if title in ky["match"]:
                result = ky
                break
        else:
            if ky["match"] == title:
                result = ky
                break

    # logger.debug("title:%s, \nmatch exact:%s"
    #              "ky in SEG_DEF: %s, result:%s" % (title, exact, ky, result))

    return result


def headlessCamel(In_put):
    # Use this to format field names:
    # Convert words to title format and remove spaces
    # Remove underscores
    # Make first character lower case
    # result result

    Camel = ''.join(x for x in In_put.title() if not x.isspace())
    Camel = Camel.replace('_', '')

    result = Camel[0].lower() + Camel[1:len(Camel)]

    # logger.debug("In_put:%s \nheadlessCamel:%s" % (In_put, result))

    return result


def is_body(ln):
    # Is line type = "BODY"

    result = False
    if key_is_in("type", ln):
        if ln["type"].upper() == "BODY":
            result = True

    # logger.debug("is_body:%s" % result)

    return result


def is_eol(ln, lst):
    # Are we at the end of the list
    # len(list) - 1

    result = False

    if ln >= len(lst) - 1:
        # line is >= items in list
        result = True

    return result


def is_head(ln):
    # Is line type = "HEADER" in ln

    result = False

    if key_is_in("type", ln):

        # logger.debug("Matching HEAD in:%s" % ln["type"])

        if "HEAD" in ln["type"].upper():
            # match on "HEAD", "HEADING" or "HEADER"
            result = True

    # logger.debug("is_header:%s" % result)

    return result


def is_multi(ln_dict):
    # Check value of "Multi" in ln_dict

    result = False

    if key_is_in("multi", ln_dict):
        multi = ln_dict["multi"].upper()
        if multi == "TRUE":
            result = True
    else:
        result = False

    # logger.debug("result:%s"
    #              "\nln_dict:%s" % (result, to_json(ln_dict)))

    return result


def key_is(ky, dt, val):
    # if KY is in DT and has VAL

    result = False

    if ky in dt:
        if isinstance(dt[ky], str):
            if dt[ky].upper() == val.upper():
                result = True

    # logger.debug("ky:", ky,
    #              "dict:", to_json(dt),
    #              "val:", val,
    #              "result:", result)
    return result


def key_is_in(ky, dt):
    # Check if key is in dict

    result = False
    if ky in dt:
        result = True

    # logger.debug("ky:%s dict:%s result:%s" % (ky, to_json(dt), result))

    return result


def key_is_in_subdict(ky, dt):
    # Check if key is in dict

    result = False

    # print("Size of dict-dt:", len(dt))

    for ctr in dt:
        # print("dt["+str(ctr)+"]", dt[ctr])
        if ky in dt[ctr]:
            key = dt[ctr]
            # print("key:", ky, " in ", dt[ctr])
            result = True
            break

    if not result:
        for key in dt.keys():
            # print("key:", key)
            if ky in key:
                # print("key:", key)
                result = True
                break

            elif isinstance(key, dict):
                for subkey, subval in key.items():
                    # print("subkey:", subkey, "subval:", subval)
                    if ky in subkey:
                        result = True
                        break

                        # end of for subkey
    # end of for key
    # logger.debug("ky:%s key:%s dict:%s "
    #              "result:%s" % (ky, key, to_json(dt), result))

    return result


def key_value(ky, dt):
    # check if key is in dict and
    # return the value of key or "" if not found
    # done to avoid key errors

    result = ""

    if ky in dt:
        result = dt[ky]

    # logger.debug("ky:%s dict:%s result:%s" % (ky, to_json(dt), result))
    return result


def overide_fieldname(lvl, match_ln, current_fld):
    # Lookup line  in SEG_DEF using match_ln[lvl]
    # look for "name" or "field"
    # if no match return current_fld
    # else return name or field
    # if name and field defined use field

    result = current_fld

    title = combined_match(lvl, match_ln)
    if find_segment(title):
        tmp_seg_def = get_segment(title)
        if key_is_in("field", tmp_seg_def):
            result = tmp_seg_def["field"]
        elif key_is_in("name", tmp_seg_def):
            result = tmp_seg_def["name"]

        # logger.debug("lvl: %s \nMatch_ln:%s"
        #              "title:%s \ntmp_seg_def:%s"
        #              "\nResult:%s" % (lvl,
        #                               match_ln,
        #                               to_json(tmp_seg_def),
        #                               title,
        #                               result))
    return result


def parse_date(d):
    # convert date to json format

    # logger.debug("Date to parse:%s" % d)
    result = ""

    d = d.strip()
    if len(d) > 0:
        # print d
        date_value = datetime.strptime(d, "%m/%d/%Y")
        result = date_value.strftime("%Y%m%d")

    # logger.debug("Result:%s" % result)

    return result


def parse_time(t):
    # convert time to  json format

    # logger.debug("Time to parse:%s" % t)
    t = t.strip()
    time_value = datetime.strptime(t, "%m/%d/%Y %I:%M %p")
    # print(time_value)
    result = time_value.strftime("%Y%m%d%H%M%S+0500")

    # logger.debug("Result:%s" % result)

    return result


def segment_prefill(wrk_seg_def, seg_dict):
    # Receive the Segment information for a header line
    # get the seg["pre"] and iterate through the dict
    # assigning to segment_dict
    # First we reset the segment_dict as an OrderedDict

    if len(seg_dict) > 0:
        # logger.debug("Pre-fill- segment_dict:%s NOT EMPTY" % seg_dict)
        pass
    else:
        seg_dict = OrderedDict()

    # logger.debug("seg:%s" % to_json(wrk_seg_def))

    cur_seg = wrk_seg_def["name"]

    if key_is_in("pre", wrk_seg_def):
        if "pre" in wrk_seg_def:
            pre = wrk_seg_def["pre"]
            for pi, pv in pre.items():
                seg_dict[pi] = pv

    # logger.debug("Current_Segment:%s segment_dict:%s" % (cur_seg, seg_dict))

    return cur_seg, seg_dict


def set_source(kvs):
    # Set the source of the data

    result = kvs["source"]
    if kvs["k"].upper() == "SOURCE":
        # print("Found Source: [%s:%s]" % (key,value))
        if kvs["v"].upper() == "SELF-ENTERED":
            result = "patient"
            kvs["v"] = result

        elif kvs["v"].upper() == "MYMEDICARE.GOV":
            result = "MyMedicare.gov"
            kvs["v"] = result

        else:
            result = kvs["v"].upper()
        # print("[%s]" % result)
        kvs["source"] = result

    return kvs


def setup_header(ln_ctrl, wrk_ln_dict):

    wrk_add_dict = {}
    seg_name = ln_ctrl["name"]
    ret_seg = ""

    # sub_kvs = {"k": "", "v": "", "source": "", "comments": [], "ln": 0}

    # sub_kvs = assign_key_value(wrk_ln_dict["line"], sub_kvs)

    if key_is_in("type", ln_ctrl):
        if ln_ctrl["type"].lower() == "list":
            wrk_add_dict[seg_name] = []
        elif ln_ctrl["type"].lower() == "dict":
            wrk_add_dict[seg_name] = OrderedDict()
            if key_is_in("pre", ln_ctrl):
                ret_seg, wrk_add_dict[seg_name] = segment_prefill(ln_ctrl, {})
        else:
            wrk_add_dict[seg_name] = wrk_ln_dict["line"]

    # logger.debug("Assigning Header========================"
    #              # "Sub_KVS:", sub_kvs,
    #              "\nfrom wrk_ln_dict:%s"
    #              "\nusing ln_ctrl:%s"
    #              "\nreturning wrk_add_dict:%s" % (to_json(wrk_ln_dict),
    #                                               to_json(ln_ctrl),
    #                                               to_json(wrk_add_dict)))

    return wrk_add_dict


def split_k_v(l):
    # split out line in to k and v split on ":"

    line_source = l.split(":")

    if len(line_source) > 1:
        k = headlessCamel(line_source[0])
        v = line_source[1].lstrip()
        v = v.rstrip()
    else:
        k = "comments"
        v = l

    return k, v


def to_json(items):
    """
    to_json
    pretty json format with indent = 4
    """
    itemsjson = json.dumps(items, indent=4)
    return itemsjson


def update_match(lvl, txt, match_ln):
    # Update the match_ln list
    # lvl = number position in match_ln
    # txt = line to check (received in headlessCamel format)
    # match_ln = list

    line = txt.split(":")
    if len(line) > 1:
        keym = line[0]

    else:
        keym = txt

    # get the line or the line up to the ":"
    # set the lvl position in the match_ln list
    match_ln[lvl] = keym

    # logger.debug("update_match(lvl, txt,"
    #              "match_ln):%s ,%s, %s \nkeym:%s \nmatch_ln"
    #              "[%s]:%s" % (lvl,
    #                           txt,
    #                           match_ln,
    #                           keym,
    #                           str(lvl),
    #                           match_ln[lvl]))

    return match_ln


def update_save_to(target, src, key, val_fld):
    # Test the target and update with source

    target_type = check_type(target)
    save_to = target

    # logger.debug("save_to:%s \nusing source:%s \n key:%s"
    #              "\nval_fld:%s and target:%s with target_"
    #              "type:%s" % (save_to, src, key, val_fld, target, target_type))

    if target_type == "DICT":
        # print(save_to[key])
        if key_is_in(key, save_to):
            if check_type(save_to[key]) == "LIST":
                save_to[key] = src[val_fld]
        else:
            save_to[key] = src[val_fld]

    elif target_type == "LIST":
        save_to = src[val_fld]
    elif target_type == "TUPLE":
        save_to[key] = {key: src[val_fld]}
    elif target_type == "STRING":
        # string_to_write = src[val_fld]
        save_to = src[val_fld]
    else:
        save_to[key] = src[val_fld]

    # logger.debug("returning save_to:%s \nusing source:%s"
    #              " and val_fld:%s"
    #              " and target:%s "
    #              " with target_type:%s" % (save_to,
    #                                        src,
    #                                        val_fld,
    #                                        target,
    #                                        target_type))

    return save_to


def write_comment(wrk_add_dict, kvs):
    # if value is assigned to comments we need to check
    # if comments already present
    # if so, add to the list

    # logger.debug("IN WRITE COMMENTS\nwrk_add_dict:"
    #              "kvs:%s" % (to_json(kvs)))

    if not key_is_in(kvs["k"], wrk_add_dict):
        # print(kvs["k"]," NOT in wrk_add_dict")
        # so initialize the comments list

        wrk_add_dict[kvs["k"]] = []

    else:
        if isinstance(wrk_add_dict[kvs["k"]], str):
            tmp_comment = wrk_add_dict[kvs["k"]]
            print("tmp_comment:", tmp_comment)
            # get the comment
            wrk_add_dict[kvs["k"]] = []
            # initialize the list
            wrk_add_dict[kvs["k"]].append(tmp_comment)

    # Now add the comment
    wrk_add_dict[kvs["k"]].append(kvs["v"])

    # kvs["comments"].append(kvs["v"])

    return wrk_add_dict


def write_proc_dl(kvs, process_dict, process_list):
    # standardize the update of Process_dict and process_list

    # Write source and comments to the dict
    if len(process_dict) < 1:
        # Do nothing
        # logger.debug("Process_dict:%s " % process_dict)
        pass
    else:
        # There is something to process
        process_dict = write_source(kvs, process_dict)
        # how long is process_list?
        last_item = len(process_list) - 1

        if key_is_in("details", process_dict):
            # logger.debug("COUNT OF LIST ITEMS:%s" % last_item)

            process_list[max(last_item, 0)]["details"] = [process_dict]

        elif key_is_in("lineNumber", process_dict):
            # logger.debug("COUNT of LIST ITEMS FOR EXTRA LINES:%s" % last_item)

            if key_is_in("details", process_list[max(last_item, 0)]):
                process_list[max(last_item, 0)]["details"].append(process_dict)

            else:
                process_list[max(last_item, 0)]["details"] = [process_dict]

        else:
            process_list.append(process_dict)
            # logger.debug("details NOT found in process_dict "
            #              "appended process_dict to process_list:%s" %
            #              process_list)

    return process_dict, process_list


def write_save_to(save_to, pd):
    # iterate through dict and add to save_to

    """

    :param save_to:
    :param pd:
    :return:
    """
    # logger.debug("pd:%s" % pd)

    # i = 0
    for item in pd.items():
        key = item[0]
        # print("key:", key)
        # val = item[1]
        # print("item:", item[1])
        save_to[key] = item[1]

    # logger.debug("pd:%s \nsave_to:%s" % (pd, to_json(save_to)))

    return save_to


def write_segment(itm, sgmnt, sgmnt_dict, ln_list, multi):
    # Write the segment to items dict

    # logger.debug("Item:%s Writing Segment:%s"
    #              "\nWriting dict:%s \nMulti:%s"
    #              "ln_list:%s" %(itm, sgmnt, sgmnt_dict, multi, ln_list))
    if multi:
        ln_list.append(sgmnt_dict)
        # print("Multi List:", ln_list)
        itm[sgmnt] = ln_list
    else:
        itm[sgmnt] = sgmnt_dict

    return itm, sgmnt_dict, ln_list


def write_source(kvs, dt):
    # Write source and comments to dt

    # logger.debug("kvs:%s"% kvs)

    if kvs["category"]:
        # write category
        dt["category"] = kvs["category"]

    if kvs["comments"]:
        # write comments
        dt["comments"] = kvs["comments"]
        # clear down comments
        kvs["comments"] = []

    if kvs["source"]:
        # write source
        dt["source"] = kvs["source"]

    if kvs["claimNumber"] and not key_is_in("claimNumber", dt):
        # write claimNumber
        dt["claimNumber"] = kvs["claimNumber"]

    return dt


def string_to_ordereddict(txt):
    #######################################
    # String_To_OrderedDict
    # Convert String to OrderedDict
    # Example String
    #    txt = "OrderedDict([('width', '600'), ('height', '100'),
    # ('left', '1250'), ('top', '980'), ('starttime', '4000'),
    # ('stoptime', '8000'), ('startani', 'random'), ('zindex', '995'),
    # ('type', 'text'), ('title', '#WXR#@TU@@Izmir@@brief_txt@'),
    # ('backgroundcolor', 'N'), ('borderstyle', 'solid'),
    # ('bordercolor', 'N'), ('fontsize', '35'),
    # ('fontfamily', 'Ubuntu Mono'), ('textalign', 'right'),
    # ('color', '#c99a16')])"
    #######################################

    tempDict = OrderedDict()

    od_start = "OrderedDict(["
    od_end = '])'

    txt = txt.decode('utf-8')
    first_index = txt.find(od_start)
    last_index = txt.rfind(od_end)

    new_txt = txt[first_index + len(od_start): last_index]
    # print("new_txt:", new_txt)
    # print("First 3:", new_txt[1:-1])

    pattern = r"(\(\'\S+\'\,\ \'\S+\'\))"
    all_variables = re.findall(pattern, new_txt)

    # print("All_var:", all_variables)
    for str_variable in all_variables:
        # print("str_variable", str_variable)
        data = str_variable.split("', '")
        key = data[0].replace("('", "")
        value = data[1].replace("')", "")
        # print("key : %s" % (key))
        # print("value : %s" % (value))
        tempDict[key] = value

    # print(tempDict)
    # print(tempDict['title'])

    return tempDict
