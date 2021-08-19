import apps.logging.request_logger as logging
import requests

from decimal import Decimal

TRUE_LIST = [1, "1", "true", "True", "TRUE", "YES", "Yes", "yes", True]
FALSE_LIST = [0, "0", "False", "FALSE", "false", "NO", "No", "no", False]


logger = logging.getLogger('hhs_server.%s' % __name__)


def bool_env(env_val):
    """ check for boolean values """

    if env_val:
        if env_val in TRUE_LIST:
            return True
        if env_val in FALSE_LIST:
            return False
        return env_val
    else:
        if env_val in FALSE_LIST:
            return False

        return


def int_env(env_val):
    """ convert to integer from String """

    return int(Decimal(float(env_val)))


def get_aws_ec2_instance_metadata():
    # Call metadata endpoint on instance to get instance & AMI ids
    try:
        token = requests.put('http://169.254.169.254/latest/api/token',
                             headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'},
                             timeout=15).text
        document = requests.get('http://169.254.169.254/latest/dynamic/instance-identity/document',
                                headers={'X-aws-ec2-metadata-token': token}).json()

        return {"imageId": document.get("imageId", "ami-00000000000000000"),
                "instanceId": document.get("instanceId", "i-00000000000000000")}

    except requests.exceptions.RequestException as err:
        # NOTE: Would normally log here, but logging is not setup yet. So print to console.
        print("WARNING: Could not get EC2 metadata in settings: " + str(err))
        return {'imageId': 'ami-00000000000000000', 'instanceId': 'i-00000000000000000'}
