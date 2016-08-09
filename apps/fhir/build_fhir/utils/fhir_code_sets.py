#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.
FILE: fhir_code_sets
Created: 7/28/16 3:27 PM

Created by: ''
"""

# https://www.hl7.org/fhir/valueset-address-use.html
FHIR_ADDRESS_USE_CODE = ['home',
                         'work',
                         'temp',
                         'old']

# https://www.hl7.org/fhir/valueset-address-type.html
FHIR_ADDRESS_TYPE_CODE = ['postal',
                          'physical',
                          'both']

# http://hl7.org/fhir/ValueSet/contact-point-system
FHIR_CONTACTPOINT_SYSTEM_CODE = ['phone',
                                 'fax',
                                 'email',
                                 'pager',
                                 'other']

# https://www.hl7.org/fhir/valueset-contact-point-use.html
FHIR_CONTACTPOINT_USE_CODE = ['home',
                              'work',
                              'temp',
                              'old',
                              'mobile']

FHIR_HUMANNAME_USE_CODE = ['usual',
                           'official',
                           'temp',
                           'nickname',
                           'anonymous',
                           'old',
                           'maiden']

FHIR_IDENTIFIER_USE_CODE = ['usual',
                            'official',
                            'temp',
                            'secondary']

FHIR_LOCATION_STATUS_CODE = ['active',
                             'suspended',
                             'inactive']

FHIR_QUANTITY_COMP_CODE = ['<', '<=', '>=', '>']
