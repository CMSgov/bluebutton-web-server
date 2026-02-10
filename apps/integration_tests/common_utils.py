import jsonschema
import re
import os
import traceback
from functools import wraps
from jsonschema import validate
from selenium.common.exceptions import NoSuchElementException


def screenshot_on_exception(func):
    """
    A decorator for getting a screenshot and html dump
    when an exception occurs in a selenium test

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
                    print(f"{'=' * 80}")
                    print(f'Current URL: {webdriver.current_url}')
                    print(f'Page Title: {webdriver.title}')

                    test_folder = os.path.join('dev-local/selenium/dump', func.__name__)
                    os.makedirs(test_folder, exist_ok=True)

                    # screenshot of failed page
                    screenshot_filename = os.path.join(test_folder, 'screenshot.png')
                    webdriver.save_screenshot(screenshot_filename)

                    # html dump of failed page
                    html_filename = os.path.join(test_folder, 'page.html')
                    with open(html_filename, 'w', encoding='utf-8') as html_file:
                        html_file.write(webdriver.page_source)

                    # error stack trace
                    error_filename = os.path.join(test_folder, 'error.txt')
                    with open(error_filename, 'w', encoding='utf-8') as error_file:
                        trace_text = ''.join(
                            traceback.format_exception(
                                type(outer_exception),
                                outer_exception,
                                outer_exception.__traceback__,
                            )
                        )
                        error_file.write(trace_text)
                except Exception as save_error:
                    print(f'Failed to capture test failure: {save_error}')
            raise outer_exception
    return wrapper


def log_step(message, level='INFO'):
    """Log a step with consistent formatting"""
    prefix = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠️'
    }.get(level, '•')

    print(f'{prefix} {message}')


def check_element_state(driver, by, by_expr, state):
    """Check and log the state of an HTML element

    Args:
        driver (webdriver): selenium webdriver instance
        by (By): locator strategy
        by_expr (str): by expression
        state (str): state at time of failure

    Returns:
        N/A
    """
    try:
        elem = driver.find_element(by, by_expr)
        exists = True
        visible = elem.is_displayed()
        enabled = elem.is_enabled()

        print(f"    🔍 Element state {state}: {by}='{by_expr}'")
        print(f'       Exists: {exists} | Visible: {visible} | Enabled: {enabled}')

        if not visible:
            print(f'       Size: {elem.size}')
            print(f'       Location: {elem.location}')
            print(f"       CSS display: {elem.value_of_css_property('display')}")
            print(f"       CSS visibility: {elem.value_of_css_property('visibility')}")
        if exists and not visible:
            print('    ⚠️  Element EXISTS but is NOT VISIBLE')
        elif exists and visible and not enabled:
            print('    ⚠️  Element EXISTS and VISIBLE but NOT ENABLED')
    except NoSuchElementException:
        print(f"    ⚠️  Element NOT FOUND in DOM: {by}='{by_expr}'")
        return (False, False, False, None)
    except Exception as e:
        print(f'    ❌ Error checking element: {e}')
        return (False, False, False, None)


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
