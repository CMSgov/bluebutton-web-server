import logging

import watchtower

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(watchtower.CloudWatchLogHandler(log_group='/bb/test/app/perf_mon.log'))

logger.info('Test log from plain Python shell')
logging.getLogger('watchtower').setLevel(logging.DEBUG)  # Turn on internal watchtower logs
