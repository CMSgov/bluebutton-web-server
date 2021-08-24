import boto3
import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import status
from rest_framework.exceptions import APIException


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
    def __init__(self):
        self.__enabled = settings.LOG_FIREHOSE_ENABLE
        self.__firehose = None

        if self.__enabled:
            self.__delivery_stream_name = settings.LOG_FIREHOSE_STREAM_NAME

            try:
                self.__firehose = boto3.client('firehose')
            except Exception as err:
                mesg = "Firehose client initialization failed. err: " + str(err)
                raise BFDInsightsFirehoseException(mesg)

    def put_message(self, message: dict):
        if self.__enabled:
            try:
                event = {
                    "instance_id": settings.AWS_EC2_INSTANCE_ID,
                    "image_id": settings.AWS_EC2_IMAGE_ID,
                    "component": "bb2.web",
                    "vpc": settings.TARGET_ENV,
                    "log_name": "audit.global_state_metrics",
                    "message": message,
                }
                self.__firehose.put_record(DeliveryStreamName=self.__delivery_stream_name,
                                           Record={'Data': json.dumps(event, cls=DjangoJSONEncoder) + '\n'})
            except Exception as err:
                mesg = "Firehose put_message() failed. err: " + str(err)
                raise BFDInsightsFirehoseException(mesg)

    def service_health_check(self):
        if self.__enabled:
            # Check for delivery stream in list as a health check.
            response = self.__firehose.list_delivery_streams()

            if self.__delivery_stream_name not in response['DeliveryStreamNames']:
                raise BFDInsightsFirehoseException("Delivery stream name not found for: " + self.__delivery_stream_name)

            return True
        else:
            raise BFDInsightsFirehoseException("Firehose is disabled in settings.LOG_FIREHOSE_ENABLE")
