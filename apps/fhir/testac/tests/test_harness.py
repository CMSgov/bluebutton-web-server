#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.
FILE: test_harness
Created: 7/27/16 8:20 AM

Created by: ''
"""


class FakeMessages:
    ''' mocks the Django message framework, makes it easier to get
        the messages out '''

    messages = []

    def add(self, level, message, extra_tags):
        self.messages.append(str(message))

    @property
    def pop(self):
        return self.messages.pop()
