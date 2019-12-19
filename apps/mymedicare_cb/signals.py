import django.dispatch

post_sls = django.dispatch.Signal(providing_args=["response"])


def response_hook(response, *args, **kwargs):
    post_sls.send_robust(None, response=response)
