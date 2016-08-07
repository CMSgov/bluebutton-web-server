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
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest


class MessagingRequest(HttpRequest):
    session = 'session'

    def __init__(self):
        super(MessagingRequest, self).__init__()
        self._messages = FallbackStorage(self)

    def add(self, level, message, extra_tags):
        print("Adding Message: %s:%s[%s]" % (level, message, extra_tags))
        return "%s:%s[%s]" % (level, message, extra_tags)

    def get_messages(self):
        return getattr(self._messages, '_queued_messages')

    def get_message_strings(self):
        return [str(m) for m in self.get_messages()]


class FakeMessages:
    ''' mocks the Django message framework, makes it easier to get
        the messages out '''

    messages = []

    def add(self, level, message, extra_tags):
        self.messages.append(str(message))

    def list(self):
        return self.messages

    @property
    def pop(self):
        return self.messages.pop()
