from django.http import JsonResponse


# Error format based on Google's JSON style guide:
# https://google.github.io/styleguide/jsoncstyleguide.xml#Reserved_Property_Names_in_the_error_object
#
# Also used by QPP as documented at:
# https://confluence.cms.gov/display/QPPGUIDE/RESTful+API+style+guide#RESTfulAPIstyleguide-JSON
def build_error_response(code, message):
    return JsonResponse({
                        "error": {
                            "code": code,
                            "message": message,
                        }},
                        status=code)


def method_not_allowed(allowed_methods):
    response = build_error_response(405, 'The method you requested is not allowed')
    response['Allow'] = ', '.join(allowed_methods)
    return response
