from django.shortcuts import render
from django.contrib import messages
import collections, json
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from .forms import CertifyingBodyForm
from .models import CertifyingBody
# Create your views here.

@login_required
def create_certifying_body(request):
    name = _("Signup as a Certifying Body")
    if request.method == 'POST':
        form = CertifyingBodyForm(request.POST)
        if form.is_valid():
            c = form.save()
            messages.success(request, _("You have been registered as a certifying body and will be contacted shortly."))  
            return HttpResponseRedirect(reverse('home'))
        else:
            #The form is invalid
             messages.error(request,_("Please correct the errors in the form."))
             return render(request,'generic/bootstrapform.html',{'form': form,
                                             'name':name,
                                             })
            
   #this is a GET
    data ={'first_name': request.user.first_name,
           'last_name': request.user.last_name,
           'email': request.user.email,
           }
    context= {'name':name,
              'form': CertifyingBodyForm(initial=data)}
    return render(request, 'generic/bootstrapform.html', context)



def certifying_bodies_as_json(request):
    l = []
    
    cbs = CertifyingBody.objects.filter(verified=True)
    
    for c in cbs:
        d = collections.OrderedDict()
        d['iss']                = c.iss
        d['title']              = c.title
        d['website']            = c.website_url
        d['public_cert_url']    = c.public_cert_url
        d['created']            = str(c.created)
        d['updated']            = str(c.updated)
        
        l.append(d)
    
    return JsonResponse(l, safe=False)
        
        
    
    
    
