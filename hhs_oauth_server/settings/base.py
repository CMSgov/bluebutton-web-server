import os

import environ

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(
    TARGET_ENV=(str, ''),
)

TARGET_ENV = env('TARGET_ENV')

if TARGET_ENV == 'local' or TARGET_ENV == 'codebuild':
    from hhs_oauth_server.settings.base_local import *
else:
    from hhs_oauth_server.settings.base_ec2 import *
