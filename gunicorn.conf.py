def post_worker_init(worker):
    import logging.config

    from django.conf import settings

    logging.config.dictConfig(settings.LOGGING)


def worker_exit(server, worker):
    import logging

    logging.shutdown()
