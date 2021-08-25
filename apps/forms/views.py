from apps.forms.models import Forms, INTERIM_PROD_ACCESS_FORM_TYPE, IN_PROGRESS_STATUS
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse
from .django_forms import InterimProdAccessForm


def interim_prod_access_view(request):
    if request.method == "POST":
        form = InterimProdAccessForm(request.POST)
        # hello world

        if form.is_valid():
            new_interim_prod_access_model = Forms(
                form_data=form.cleaned_data,
                type=INTERIM_PROD_ACCESS_FORM_TYPE,
                status=IN_PROGRESS_STATUS,
            )
            new_interim_prod_access_model.save()
            id = new_interim_prod_access_model.id
            return HttpResponseRedirect(
                reverse("existing-interim-prod-access", args=(id))
            )

    else:
        if request.user:
            form = Forms.objects.get(user=request.user)
        else:
            form = InterimProdAccessForm()

    context = {}
    context["form"] = form
    return render(request, "interim_prod_access.html", context)
