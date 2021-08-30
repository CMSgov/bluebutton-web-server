from libs.mail import Mailer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from apps.forms.models import (
    Forms,
    INTERIM_PROD_ACCESS_FORM_TYPE,
    IN_PROGRESS_STATUS,
    SUBMITTED_STATUS,
)
from django.shortcuts import render
from .django_forms import InterimProdAccessForm

DEFAULT_EMAIL_SEND_ADDRESS = "bluebuttonapi@cms.hhs.gov"


class InterimProdAccessView(LoginRequiredMixin, TemplateView):
    template_name = "interim_prod_access.html"

    def form_diff(self, original_form_data, updated_form_data):
        form_differences = {}

        for key in updated_form_data:
            if original_form_data[key] != updated_form_data[key]:
                form_differences[key] = {
                    "before": original_form_data[key],
                    "after": updated_form_data[key],
                }

        return form_differences

    def send_mail(self, context, app_name="Unknown"):
        mailer = Mailer(
            subject="Interim Prod Access: " + app_name,
            template_text="interim_prod_access_email.txt",
            template_html="interim_prod_access_email.html",
            to=[
                DEFAULT_EMAIL_SEND_ADDRESS,
            ],
            context=context,
        )
        mailer.send()

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, "interim_prod_access.html", context)

    def post(self, request, *args, **kwargs):
        form = InterimProdAccessForm(request.POST)
        context = self.get_context_data()

        if form.is_valid():
            if context["form_model"] is None:
                interim_prod_access_model = Forms(
                    form_data=form.cleaned_data,
                    user=request.user,
                    type=INTERIM_PROD_ACCESS_FORM_TYPE,
                    status=IN_PROGRESS_STATUS,
                )
                interim_prod_access_model.save()
                self.send_mail(
                    {"form_data": form.cleaned_data},
                    form.cleaned_data["application_name"],
                )
                self.update_context_display(context, form.cleaned_data)
                context["action"] = "created"
            else:
                if context["form_model"].status is SUBMITTED_STATUS:
                    context["action"] = "submitted"
                else:
                    original_data = context["form_model"].form_data
                    context["form_model"].form_data = form.cleaned_data
                    context["form_model"].save()
                    context["action"] = "updated"
                    form_data_diff = self.form_diff(original_data, form.cleaned_data)
                    self.send_mail(
                        {"form_data": form_data_diff},
                        form.cleaned_data["application_name"],
                    )
                    self.update_context_display(context, form.cleaned_data)

            return self.render_to_response(context)

    def update_context_display(self, context, new_form_data):
        context["form_display"] = InterimProdAccessForm(new_form_data)

    def get_context_data(self, **kwargs):
        request = self.request

        try:
            form_model = Forms.objects.get(user=request.user)
            form_display = InterimProdAccessForm(form_model.form_data)
        except Forms.DoesNotExist:
            form_model = None
            form_display = InterimProdAccessForm()

        context = {"form_model": form_model, "form_display": form_display}
        return context
