import jsonschema
import re

from jsonschema import validate


def validate_json_schema(schema, content):
    try:
        validate(instance=content, schema=schema)
    except jsonschema.exceptions.ValidationError:
        return False
    return True


def extract_href_from_html(html):
    # Regular expression patterns
    # title_pattern = r'title="([^"]*)"'
    href_pattern = r'href="([^"]*)"'

    # Search for title and href attributes
    # title_match = re.search(title_pattern, html)
    href_match = re.search(href_pattern, html)

    # title = title_match.group(1) if title_match else None
    href = href_match.group(1) if href_match else None

    return href


def extract_last_part_of_url(url):
    # Split the URL by '/' and get the last part
    parts = url.rstrip('/').split('/')
    last_part = parts[-1]

    return last_part
