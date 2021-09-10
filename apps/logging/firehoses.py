import boto3
import json

from datetime import datetime
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.logging.utils import format_timestamp

"""
  Firehose class for BFD-Insights connectivity
"""


class BFDInsightsFirehoseException(APIException):
    # BB2-130 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class BFDInsightsFirehose():
    """
    Firehose class for use in apps.logging.loggers.log_global_state_metrics().
    """
    def __init__(self, firehose_name_postfix):
        self.__enabled = settings.LOG_FIREHOSE_ENABLE
        self.__firehose = None

        if self.__enabled:
            self.__delivery_stream_name = settings.LOG_FIREHOSE_STREAM_NAME_PREFIX + firehose_name_postfix

            try:
                # create an STS client object that represents a live connection to the STS service
                sts_client = boto3.client('sts')

                # Call the assume_role method
                assumed_role_object = sts_client.assume_role(
                    RoleArn=settings.LOG_FIREHOSE_CROSSOVER_ROLE_ARN,
                    RoleSessionName="AssumeRoleSession"
                )

                # From the response that contains the assumed role, get the temporary credentials
                credentials = assumed_role_object['Credentials']

                # Use the temporary credentials that AssumeRole returns to make a connection to firehose
                self.__firehose = boto3.client(
                    'firehose', region_name=settings.AWS_DEFAULT_REGION,
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken'],
                )
            except Exception as err:
                mesg = "Firehose client initialization failed. err: " + str(err)
                raise BFDInsightsFirehoseException(mesg)

    def put_message(self, message: dict):
        if self.__enabled:
            time_of_event = format_timestamp(datetime.now())

            try:
                event = {
                    "time_of_event": time_of_event,
                    "instance_id": settings.AWS_EC2_INSTANCE_ID,
                    "image_id": settings.AWS_EC2_IMAGE_ID,
                    "component": "bb2.web",
                    "vpc": settings.TARGET_ENV,
                    "log_name": "audit.global_state_metrics",
                }
                event.update(message)
                self.__firehose.put_record(DeliveryStreamName=self.__delivery_stream_name,
                                           Record={'Data': json.dumps(event, cls=DjangoJSONEncoder) + '\n'})
            except Exception as err:
                mesg = "Firehose put_message() failed. err: " + str(err)
                raise BFDInsightsFirehoseException(mesg)
