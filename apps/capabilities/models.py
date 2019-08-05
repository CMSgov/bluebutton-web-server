import json
import re

from django.db import models
from django.contrib.auth.models import Group
from django.utils.lru_cache import lru_cache
from django.db.models import CASCADE


class ProtectedCapability(models.Model):
    title = models.CharField(max_length=255,
                             default='',
                             unique=True)
    slug = models.CharField(verbose_name='Scope',
                            max_length=255,
                            default='',
                            unique=True)
    group = models.ForeignKey(Group, on_delete=CASCADE,)
    description = models.TextField(max_length=10240,
                                   blank=True,
                                   default='')
    protected_resources = models.TextField(
        help_text="""A JSON list of pairs containing HTTP method and URL.
        It may contain [id] placeholders for wildcards
        Example: [["GET","/api/task1"], ["POST","/api/task2/[id]"]]""",
        default="""[["GET", "/some-url"]]"""
    )

    default = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def resources_as_dict(self):
        """
        Return protected_resources mapped into a dictionary.
        e.g. {"GET": ["/api/example1", "/api/example2"], "POST": ... }
        """
        protected_resources = {}
        for method, path in json.loads(self.protected_resources):
            if method not in protected_resources:
                protected_resources[method] = [path]
            else:
                protected_resources[method].append(path)
        return protected_resources

    def allow(self, method, path):
        """
        Check if the capability allow access for `method` and `path`.
        """
        resources = self.resources_as_dict()
        for allowed_path in resources.get(method, []):
            if _match(path, allowed_path):
                return True
        return False

    def scope(self):
        return self.slug

    def save(self, *args, **kwargs):
        super(ProtectedCapability, self).save(**kwargs)

    class Meta:
        verbose_name_plural = 'Protected Capabilities'
        verbose_name = 'Protected Capability'


@lru_cache()
def _tokenize_path(path):
    """
    Helper function that removes trailing slash
    and split the path into bits.

    e.g.: "/api/foo/" -> ["", "api", "foo"]
    """
    return path.rstrip("/").split("/")


URL_BIT_PATTERN = re.compile(r"\[.*\]")


@lru_cache()
def _match(request_path, allowed_path):
    """
    Helper function that check if request_path matches with allowed_path
    """
    # normalize and tokenize both paths
    # from '/api/foo' to ['', 'api', 'foo']
    request_tokens = _tokenize_path(request_path)
    allowed_tokens = _tokenize_path(allowed_path)

    # if the number of tokens is different we know
    # that the request path does not match the allowed path
    if len(request_tokens) != len(allowed_tokens):
        return False

    # otherwise we start the comparison token by token
    for request_token, allowed_token in zip(request_tokens, allowed_tokens):
        # if the allowed token matches a pattern like "[id]"
        # the match is valid and move to the next token
        if URL_BIT_PATTERN.match(allowed_token):
            continue

        # we can break the loop and return False
        # when we encounter the first non-matching token
        if request_token != allowed_token:
            return False

    return True
