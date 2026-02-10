import environ
import os

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(
    IS_LOCAL=(bool, False),
)

environ.Env.read_env(os.path.join(BASE_DIR + '/dev-local', '.env.local'))

IS_LOCAL = env.bool("IS_LOCAL", default=False)

if IS_LOCAL:
    from .base_local import * # noqa
else:
    from .base_ec2 import * # noqa
