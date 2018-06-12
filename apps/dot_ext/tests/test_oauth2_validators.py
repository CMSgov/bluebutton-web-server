from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.dot_ext.validators import validate_uris


class TestOauth2Validators(TestCase):
    def test_validate_uris(self):
        with self.assertRaises(ValidationError):
            validate_uris('ftp://example.com/redirect')

        with self.assertRaises(ValidationError):
            validate_uris('https://example.com/redirect ftp://example')

        with self.assertRaises(ValidationError):
            validate_uris('ftp://example https://example.com/redirect')

        with self.assertRaises(ValidationError):
            validate_uris('https://example.com/redirect#tag ftp://example')

        # These don't return anything, so just run them to check for exceptions
        validate_uris('https://example.com/redirect')
        validate_uris('https://example.com/redirect https://example.org/redirect')
        validate_uris('http://example.com/redirect\nhttps://example.org/redirect')
        validate_uris('http://example.com/redirect\nhttps://example.org/redirect   ' * 72)
