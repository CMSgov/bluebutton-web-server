import hashlib
from django.conf import settings
from django.core.files.storage import default_storage


# Saves a logo image to default storage
def store_logo_image(logo_image, app_pk):
    uri = None
    if logo_image:
        if getattr(logo_image, 'name', False):
            file_path = "applications/" + hashlib.sha256(str(app_pk).encode('utf-8')).hexdigest() + "/logo.jpg"
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
            default_storage.save(file_path, logo_image)
            if default_storage.exists(file_path):
                uri = settings.MEDIA_URL + file_path
    return uri
