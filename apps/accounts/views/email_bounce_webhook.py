from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from ..models import EmailWebhook


@csrf_exempt
def record_email_bounce(request):

    # print("RB:", request.body)
    ew = EmailWebhook()
    ew.save(request_body=request.body)

    return HttpResponse("OK")
