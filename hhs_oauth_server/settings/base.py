import environ
import os

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(
    TARGET_ENV=(str, ""),
)

environ.Env.read_env(os.path.join(BASE_DIR + '/dev-local', '.env.local'))

TARGET_ENV = env("TARGET_ENV", default="")

if TARGET_ENV == 'local':
    from .base_local import * # noqa
else:
    from .base_ec2 import * # noqa
