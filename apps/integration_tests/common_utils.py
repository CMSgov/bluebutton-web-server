import jsonschema

from jsonschema import validate


def validate_json_schema(schema, content):
    try:
        validate(instance=content, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        # Show error info for debugging
        print("jsonschema.exceptions.ValidationError: ", e)
        return False
    return True
