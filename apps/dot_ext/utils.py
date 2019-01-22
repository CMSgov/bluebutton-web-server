import os
import uuid
from django.conf import settings
from django.utils.deconstruct import deconstructible


# Using @deconstructible to avoid migration issue from: https://code.djangoproject.com/ticket/22999
@deconstructible
class LogoImageFilename(object):

    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        if instance.logo_image.path:
            print("-----------------before new filename path: ", instance.logo_image.path)
        filename = self.path + '/logo-' + str(uuid.uuid4()) + '.jpg'
        full = os.path.join(settings.MEDIA_ROOT, filename)

        if os.path.exists(full):
            os.remove(full)

        return filename


logo_image_filename = LogoImageFilename("logos")
