import django.dispatch

post_sls = django.dispatch.Signal()


def response_hook_wrapper(*wrapper_args, **wrapper_kwargs):
    def response_hook(response, *req_args, **req_kwargs):
        post_sls.send_robust(wrapper_kwargs['sender'],
                             response=response,
                             request=wrapper_kwargs['request'])
        return response
    return response_hook
