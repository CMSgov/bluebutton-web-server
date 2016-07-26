#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
apps.fhir.testac
FILE: forms
Created: 7/25/16 4:21 PM

File created by: Mark Scrimshire @ekivemark
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from .utils.sample_data_bb import SAMPLE_BB_TEXT

FORMAT_OUT = (('html', 'HTML'), ('json', 'JSON'))

sample_bbtext = SAMPLE_BB_TEXT


class input_packet(forms.Form):
    """ get blue button text as input """

    bb_text = forms.CharField(max_length=163840,
                              widget=forms.Textarea,
                              initial=sample_bbtext,
                              label=_('Bluebutton Text'),
                              help_text=_('Paste in the contents of your '
                                          'Blue Button text file here.'))

    output_format = forms.ChoiceField(choices=FORMAT_OUT,
                                      required=True,
                                      initial='html',
                                      label="Output Format:")
