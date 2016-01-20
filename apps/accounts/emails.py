#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from django.core.mail import EmailMessage,  EmailMultiAlternatives


def send_password_reset_url_via_email(user, reset_key):
    if settings.SEND_EMAIL:
        subject = "[%s]Your password reset request" % (settings.ORGANIZATION_NAME)    
        from_email = settings.EMAIL_HOST_USER
        to = user.email
        headers = {'Reply-To': from_email}
        
        html_content = """"
        <P>
        Click on the following link to reset your password.<br>
        <a HREF="%s/accounts/reset-password/%s">%s/accounts/reset-password/%s</a>
        </p>
        <p>
        Thank you,
        </p>
        <p>
        The NPPES Modernization Team
        
        </P>
        """ % (settings.HOSTNAME_URL , reset_key, settings.HOSTNAME_URL, reset_key)
       
        text_content="""
        Click on the following link to reset your password.
        %s/accounts/reset-password/%s
        
        
        Thank you,
        
        The NPPES Modernization Team
        
        """ % (settings.HOSTNAME_URL , reset_key,)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to,])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


def send_signup_key_via_email(user, signup_key):
    
    
    if settings.SEND_EMAIL:
        subject = "[%s]Verify your email to get started." % (settings.ORGANIZATION_NAME)    
        from_email = settings.EMAIL_HOST_USER
        to = user.email
        headers = {'Reply-To': from_email}
        
        html_content = """
        <P>
        You're almost done.  Please click the link to activate your account.<br>
        <a HREF="%s/accounts/signup-verify/%s">%s/accounts/signup-verify/%s</a>
        
        Thank you,
        
        The NPPES Modernization Team
        </P>
        """ % (settings.HOSTNAME_URL, signup_key, settings.HOSTNAME_URL, signup_key)
       
        text_content="""
        You're almost done.  Please click the link to activate your account.
        %s/accounts/signup-verify/%s
        
        Thank you,
        
        The NPPES Modernization Team
        
        
        """ % (settings.HOSTNAME_URL, signup_key,)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to,])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


def send_invite_request_notices(invite_request):
    if settings.SEND_EMAIL:
        subject = "[%s]Invitation Request Received" % (settings.ORGANIZATION_NAME)    
        from_email = settings.EMAIL_HOST_USER
        to = invite_request.email 
        headers = {'Reply-To': from_email}
        
        html_content = """
        <p>
        Hello: %s %s,
        </p>
        <p>
        Your request for an invite to Enumeration API (%s) has been received.
        </p>
        <p>
        Thank You,
        </p>
        <p>
        The NPPES Modernization Team
        </p>
        """ % (invite_request.first_name,
               invite_request.last_name,
               settings.HOSTNAME_URL, )
       
        text_content="""Hello: %s %s,
    Your request for an invite to Enumeration API (%s) has been received.
        """ % (invite_request.first_name,
               invite_request.last_name,
               settings.HOSTNAME_URL, )
        msg = EmailMultiAlternatives(subject, text_content, from_email,
                                     [to,settings.INVITE_REQUEST_ADMIN, ])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    

