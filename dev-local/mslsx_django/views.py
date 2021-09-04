import json
import base64

from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urlencode


signed_in = True

ENCODE_NAME = "ascii"

ID_FIELD = "id"
USERNAME_FIELD = "username"
NAME_FIELD = "name"
EMAIL_FIELD = "email"
FIRST_NAME_FIELD = "fisrt_name"
LAST_NAME_FIELD = "last_name"
HICN_FIELD = "hicn"
MBI_FIELD = "mbi"
CODE_KEY = "code"
AUTH_HEADER = "Authorization"


def _base64_encode(string):
    """
    Removes any `=` used as padding from the encoded string.
    """
    encoded = base64.urlsafe_b64encode(string)
    return encoded.rstrip(b"=")


def _base64_decode(string):
    """
    Adds back in the required padding before decoding.
    """
    padding = 4 - (len(string) % 4)
    string = string + ("=" * padding)
    return base64.urlsafe_b64decode(string)


def _encode(usr="", name="", first_name="", last_name="", email="", hicn="", mbi=""):
    return "{}.{}.{}.{}.{}.{}.{}".format(_base64_encode(usr.encode(ENCODE_NAME)).decode(ENCODE_NAME),
                                         _base64_encode(name.encode(ENCODE_NAME)).decode(ENCODE_NAME),
                                         _base64_encode(first_name.encode(ENCODE_NAME)).decode(ENCODE_NAME),
                                         _base64_encode(last_name.encode(ENCODE_NAME)).decode(ENCODE_NAME),
                                         _base64_encode(email.encode(ENCODE_NAME)).decode(ENCODE_NAME),
                                         _base64_encode(hicn.encode(ENCODE_NAME)).decode(ENCODE_NAME),
                                         _base64_encode(mbi.encode(ENCODE_NAME)).decode(ENCODE_NAME))


def _decode(b64code):
    flds = b64code.split(".")
    return {
        "usr": _base64_decode(flds[0]).decode(ENCODE_NAME),
        "name": _base64_decode(flds[1]).decode(ENCODE_NAME),
        "first_name": _base64_decode(flds[2]).decode(ENCODE_NAME),
        "last_name": _base64_decode(flds[3]).decode(ENCODE_NAME),
        "email": _base64_decode(flds[4]).decode(ENCODE_NAME),
        "hicn": _base64_decode(flds[5]).decode(ENCODE_NAME),
        "mbi": _base64_decode(flds[6]).decode(ENCODE_NAME),
    }


def login_page(request):
    '''
    response with login form
    '''
    return render(request, 'login.html', {
        "relay": request.GET.get("relay", "missing"),
        "redirect_uri": request.GET.get("redirect_uri", "missing"),
    })


def login(request):
    '''
    process login form POST, collect sub, mbi, hicn, etc.
    '''

    redirect_url = request.POST.get("redirect_uri", None)

    req_token = _encode(request.POST.get(USERNAME_FIELD, ""),
                        request.POST.get(NAME_FIELD, ""),
                        request.POST.get(FIRST_NAME_FIELD, ""),
                        request.POST.get(LAST_NAME_FIELD, ""),
                        request.POST.get(EMAIL_FIELD, ""),
                        request.POST.get(HICN_FIELD, ""),
                        request.POST.get(MBI_FIELD, ""))

    qparams = {
        "req_token": req_token,
        "relay": request.POST.get("relay", "")
    }
    return redirect("{}?{}".format(redirect_url, urlencode(qparams)))


def health(request):
    '''
    always good
    '''
    return HttpResponse(json.dumps({"message": "all's well"}),
                        status=200, content_type='application/json')


@csrf_exempt
def token(request):
    '''
    grant access token to further get userinfo
    '''
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    request_token = body.get("request_token", None)

    if request_token is None:
        return HttpResponse(json.dumps({"message": "Bad Request, missing request token."}),
                            status=400, content_type='application/json')

    user_info = _decode(request_token)

    token = {
        "user_id": user_info['usr'],
        "auth_token": request_token,
    }

    return HttpResponse(json.dumps(token), status=200, content_type='application/json')


def userinfo(request):

    global signed_in

    if signed_in is True:
        tkn = request.headers.get(AUTH_HEADER, None)
        if tkn is None:
            return HttpResponse(json.dumps({"message": "Bad Request, missing request token."}),
                                status=400, content_type='application/json')
        if not tkn.startswith("Bearer "):
            return HttpResponse(json.dumps({"message": "Bad Request, malformed bearer token."}),
                                status=400, content_type='application/json')
        tkn = tkn.split()[1]
        user_info = _decode(tkn)
        slsx_userinfo = {
            "data": {
                "user": {
                    "id": user_info["usr"],
                    "username": user_info["name"],
                    "email": user_info["email"],
                    "firstName": user_info["first_name"],
                    "lastName": user_info["last_name"],
                    "hicn": user_info["hicn"],
                    "mbi": user_info["mbi"],
                },
            },
        }
        signed_in = False
        return HttpResponse(json.dumps(slsx_userinfo), status=200, content_type='application/json')
    else:
        signed_in = True
        return HttpResponse(status=403, content_type='application/json')


def signout(request):
    return HttpResponse(status=302, content_type='application/json')
