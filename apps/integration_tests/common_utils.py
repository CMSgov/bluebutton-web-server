import jsonschema
import re
import os
from functools import wraps
from datetime import datetime
from jsonschema import validate


def screenshot_on_exception(func):
    """A decorator for getting a screenshot when an exception occurs in a selenium test

    Args:
        func (function): default param for decorator

    Raises:
        outer_exception: the exception thrown by the decorated function
    Returns:
        _type_: N/A
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as outer_exception:
            webdriver = getattr(self, 'driver')
            # Make sure there is a webdriver and we are not in an AWS environment
            if webdriver and os.getenv('TARGET_ENV') == 'dev':
                try:
                    test_folder = os.path.join('screenshots', func.__name__)
                    os.makedirs(test_folder, exist_ok=True)

                    # Delete oldest screenshot if 3 exist already, keep it unclutterred
                    screenshots = sorted([png for png in os.listdir(test_folder)])
                    if len(screenshots) >= 3:
                        os.remove(os.path.join(test_folder, screenshots[0]))

                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = os.path.join(test_folder, f'{timestamp}.png')
                    webdriver.save_screenshot(filename)
                except Exception as screenshot_error:
                    print(f"Failed to capture screenshot: {screenshot_error}")
            raise outer_exception
    return wrapper


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
