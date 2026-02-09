# import os

IS_LOCAL = True

if IS_LOCAL:
    from .base_local import * # noqa
else:
    from .base_ec2 import * # noqa
