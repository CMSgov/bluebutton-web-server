from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.dot_ext.validators import validate_url


class ValidateURLTests(TestCase):
    def test_valid_urls(self):
        valid_urls = [
            "https://example.com",
            "https://foo.bar/baz",
            "https://sub.domain.co.uk/path?query=1",
        ]
        for url in valid_urls:
            try:
                validate_url(url)
            except ValidationError:
                self.fail(f"validate_url() raised ValidationError unexpectedly for {url}")

    def test_invalid_urls(self):
        invalid_urls = [
            "not-a-url",
            "example",
            "http://",
            "://example.com",
            "javascript:alert(document.cookie)",
            "javascript:alert(document.domain)",
            "https://localhost",
            "http://localhost",
            " ",
        ]
        for url in invalid_urls:
            with self.assertRaises(ValidationError, msg=f"Expected failure for {url}"):
                validate_url(url)

    def test_empty_value_allowed(self):
        """Empty values should pass without raising error"""
        try:
            validate_url("")
            validate_url(None)
        except ValidationError:
            self.fail("validate_url() raised ValidationError for empty value")
