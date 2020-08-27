import django.dispatch

post_sls = django.dispatch.Signal(providing_args=["response"])


def response_hook_wrapper(*wrapper_args, **wrapper_kwargs):
    def response_hook(response, *req_args, **req_kwargs):
        post_sls.send_robust(wrapper_kwargs['sender'], response=response, auth_uuid=wrapper_kwargs['auth_uuid'])
        return response
    return response_hook
