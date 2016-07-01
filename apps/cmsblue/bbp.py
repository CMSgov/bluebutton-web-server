#!/usr/bin/env python

# An Bluebutton parser command line utility.
# Alan Viars, Videntity 2011
# Added CMS v2.0 BlueButton parsing by Mark Scrimshire (@ekivemark), 2015

import sys

# from cmsblue.parse import *
from apps.cmsblue.parse import *
from apps.cmsblue.cms_parser import *

if __name__ == "__main__":
    """
    Accept a singe VA cmsblue file and convert it into json.  Return the
    whole parsed file (all), or just a subset (i.e. bp)
    """
    try:
        outtype = sys.argv[1]
        infile = sys.argv[2]
        outfile = sys.argv[3]
        if len(sys.argv) == 5:
            level = int(sys.argv[4])
    except IndexError:
        print("You must supply an an infile and an outfile.")
        print("Example: bbp.py ",)
        print("[all|bp|wt|mds|segments|cmsblue|CMS|CMSFILE]",
              "bluebutton_infile.txt ",
              "bluebutton_outfile.json [level]")
        exit(1)

    try:
        items = simple_parse(infile)

        if outtype == "all":
            print(tojson(items))

        if outtype == "bp":
            bpdictlist = build_bp_readings(items)
            print(tojson(bpdictlist))

        if outtype == "wt":
            wtdictlist = build_wt_readings(items)
            print(tojson(wtdictlist))

        if outtype == "mds":
            mdsdictlist = build_mds_readings(items)
            print(tojson(mdsdictlist))

        if outtype == "d":
            demodict = build_simple_demographics_readings(items)
            print(tojson(demodict))

        if outtype == "segments":
            demodict = section_parse(infile)
            # print(tojson(demodict))
            result = write_file(demodict, outfile)

        if outtype == "cmsblue":
            demodict = bb_file_parse(infile)
            result = write_file(demodict, outfile)

        if outtype == "CMS":
            # demodict = cms_file_parse(infile)
            demodict = cms_file_parse2(infile)
            result = write_file(demodict, outfile)

        if outtype == "CMSFILE":
            demodict = cms_file_read(infile)
            outdict = parse_lines(demodict)
            result = write_file(outdict, outfile)

        if outtype == "CMSDICT":
            # Det the interim file
            demodict = cms_file_read(infile)

            result = write_file(demodict, outfile)

    except():
        print("An unexpected error occurred. Here is the post-mortem:")
        print(sys.exc_info())
