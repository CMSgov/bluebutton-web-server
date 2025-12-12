import jsonschema
import re
from functools import wraps
from datetime import datetime
import os
from jsonschema import validate


def screenshot_on_exception(f):
    @wraps(f)
    def take_screenshot_on_failure(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except Exception as outer_exception:
            # If an exception occurs, get a screenshot
            webdriver = getattr(self, 'driver')
            if webdriver:
                try:
                    os.makedirs('screenshots', exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'screenshots/{self.__class__.__name__}_{f.__name__}_{timestamp}.png'
                    webdriver.save_screenshot(filename)
                    print(f"Screenshot saved: {filename}")
                except Exception as screenshot_error:
                    print(f"Failed to capture screenshot: {screenshot_error}")
            raise outer_exception
    return take_screenshot_on_failure


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
