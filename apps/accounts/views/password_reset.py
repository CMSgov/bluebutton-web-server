from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from random import randint
from ..forms import (ChangeSecretQuestionsForm, PasswordResetForm,
                     PasswordResetRequestForm, SecretQuestionForm)
from ..models import UserProfile, ValidPasswordResetKey
from django.contrib.auth import authenticate, login


def reset_password(request):

    name = _('Reset Password')
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                request.user.set_password(data['password1'])
                request.user.save()
                user = authenticate(request=request,
                                    username=request.user.username,
                                    password=data['password1'])
                login(request, user)
                messages.success(request, 'Your password was updated.')
                return HttpResponseRedirect(reverse('account_settings'))
            else:
                return render(request, 'generic/bootstrapform.html',
                              {'form': form, 'name': name})
        # this is a GET
        return render(request, 'generic/bootstrapform.html',
                      {'form': PasswordResetForm(), 'name': name})
    else:
        return HttpResponseRedirect(reverse('home'))


def password_reset_email_verify(request, reset_password_key=None):
    vprk = get_object_or_404(ValidPasswordResetKey,
                             reset_password_key=reset_password_key)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            vprk.user.set_password(form.cleaned_data['password1'])
            vprk.user.save()
            vprk.delete()
            logout(request)
            messages.success(request, _('Your password has been reset.'))
            return HttpResponseRedirect(reverse('mfa_login'))
        else:
            return render(request,
                          'generic/bootstrapform.html',
                          {'form': form,
                           'reset_password_key': reset_password_key})

    return render(request,
                  'generic/bootstrapform.html',
                  {'form': PasswordResetForm(),
                   'reset_password_key': reset_password_key})


def forgot_password(request):
    name = _('Forgot Password')
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            try:
                u = User.objects.get(email=data['email'])
            except(User.DoesNotExist):
                messages.error(request,
                               'A user with the email supplied '
                               'does not exist.')
                return HttpResponseRedirect(reverse('forgot_password'))
            # success - user found so ask some question
            return HttpResponseRedirect(reverse('secret_question_challenge',
                                                args=(u.username,)))
        else:
            return render(request,
                          'generic/bootstrapform.html',
                          {'name': name, 'form': form})
    else:
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name, 'form': PasswordResetRequestForm()})


@login_required
def change_secret_questions(request):
    up = get_object_or_404(UserProfile, user=request.user)

    name = _('Change Secret Questions')
    if request.method == 'POST':
        form = ChangeSecretQuestionsForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            up.password_reset_question_1 = data['password_reset_question_1']
            up.password_reset_answer_1 = data['password_reset_answer_1']
            up.password_reset_question_2 = data['password_reset_question_2']
            up.password_reset_answer_2 = data['password_reset_answer_2']
            up.password_reset_question_3 = data['password_reset_question_3']
            up.password_reset_answer_3 = data['password_reset_answer_3']
            up.save()
            messages.success(request,
                             _("Your secret questions and answers were updated."))
            return HttpResponseRedirect(reverse('account_settings'))
        else:
            return render(request,
                          'generic/bootstrapform.html',
                          {'name': name, 'form': form})

    else:
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name,
                       'form': ChangeSecretQuestionsForm(
                           initial={'password_reset_question_1': up.password_reset_question_1,
                                    'password_reset_answer_1': up.password_reset_answer_1,
                                    'password_reset_question_2': up.password_reset_question_2,
                                    'password_reset_answer_2': up.password_reset_answer_2,
                                    'password_reset_question_3': up.password_reset_question_3,
                                    'password_reset_answer_3': up.password_reset_answer_3}
                       )})


def secret_question_challenge(request, username):
    r = randint(1, 3)
    if r == 1:
        return HttpResponseRedirect(reverse('secret_question_challenge_1',
                                            args=(username,)))
    if r == 2:
        return HttpResponseRedirect(reverse('secret_question_challenge_2',
                                            args=(username,)))
    if r == 3:
        return HttpResponseRedirect(reverse('secret_question_challenge_3',
                                            args=(username,)))


def secret_question_challenge_1(request, username):
    up = get_object_or_404(UserProfile, user__username=username)

    if request.method == 'POST':
        form = SecretQuestionForm(request.POST)
        if form.is_valid():
            # Does the answer match?
            data = form.cleaned_data
            if up.password_reset_answer_1.lower() == data['answer'].lower():
                ValidPasswordResetKey.objects.create(user=up.user)
                messages.info(request,
                              'Please check your email for a special link'
                              ' to reset your password.')
                return HttpResponseRedirect(reverse('mfa_login'))
            else:
                messages.error(request,
                               'Wrong answer. Please try again.')
                return HttpResponseRedirect(reverse('secret_question_challenge',
                                                    args=(username,)))

    # HTTP GET
    return render(request,
                  'generic/bootstrapform.html',
                  {'name': up.get_password_reset_question_1_display(),
                   'form': SecretQuestionForm()})


def secret_question_challenge_2(request, username):
    up = get_object_or_404(UserProfile, user__username=username)

    if request.method == 'POST':
        form = SecretQuestionForm(request.POST)
        if form.is_valid():
            # Does the answer match?
            data = form.cleaned_data
            if up.password_reset_answer_2.lower() == data['answer'].lower():
                ValidPasswordResetKey.objects.create(user=up.user)
                messages.info(request,
                              'Please check your email for a special link'
                              ' to reset your password.')
                return HttpResponseRedirect(reverse('mfa_login'))
            else:
                messages.error(request,
                               'Wrong answer. Please try again.')
                return HttpResponseRedirect(reverse('secret_question_challenge',
                                                    args=(username,)))
    # HTTP GET
    return render(request,
                  'generic/bootstrapform.html',
                  {'name': up.get_password_reset_question_2_display(),
                   'form': SecretQuestionForm()})


def secret_question_challenge_3(request, username):
    up = get_object_or_404(UserProfile, user__username=username)
    if request.method == 'POST':
        form = SecretQuestionForm(request.POST)
        if form.is_valid():
            # Does the answer match?
            data = form.cleaned_data
            if up.password_reset_answer_3.lower() == data['answer'].lower():
                ValidPasswordResetKey.objects.create(user=up.user)
                messages.info(request,
                              'Please check your email for a special link'
                              ' to reset your password.')
                return HttpResponseRedirect(reverse('mfa_login'))
            else:
                messages.error(request,
                               'Wrong answer. Please try again.')
                return HttpResponseRedirect(reverse('secret_question_challenge',
                                                    args=(username,)))
    # HTTP GET
    return render(request,
                  'generic/bootstrapform.html',
                  {'name': up.get_password_reset_question_3_display(),
                   'form': SecretQuestionForm()})
