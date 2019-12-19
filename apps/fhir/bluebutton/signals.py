import django.dispatch

pre_fetch = django.dispatch.Signal(providing_args=["request"])
post_fetch = django.dispatch.Signal(providing_args=["request", "response"])
