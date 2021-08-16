import boto3
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException


"""
  Firehose class for BFD-Insights connectivity
"""


class BFDInsightsFirehoseException(APIException):
    # BB2-130 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class BFDInsightsFirehoseDeliveryStreamHandler(logging.StreamHandler):
    """
    Firehose stream handler class for use in Python logging and /health/firehose health check.
    """
    def __init__(self):
        # By default, logging.StreamHandler uses sys.stderr if stream parameter is not specified
        logging.StreamHandler.__init__(self)

        self.__firehose = None
        self.__stream_buffer = []

        try:
            self.__firehose = boto3.client('firehose')
        except Exception as err:
            mesg = "Firehose client initialization failed. err: " + str(err)
            raise BFDInsightsFirehoseException(mesg)

        self.__delivery_stream_name = settings.LOG_FIREHOSE_STREAM_NAME

    def emit(self, record):
        try:
            msg = self.format(record)

            if self.__firehose:
                self.__stream_buffer.append({
                    'Data': msg.encode(encoding="UTF-8", errors="strict")
                })
            else:
                stream = self.stream
                stream.write(msg)
                stream.write(self.terminator)

            self.flush()
        except Exception:
            self.handleError(record)

    def flush(self):
        self.acquire()

        try:
            if self.__firehose and self.__stream_buffer:
                self.__firehose.put_record_batch(
                    DeliveryStreamName=self.__delivery_stream_name,
                    Records=self.__stream_buffer
                )

                self.__stream_buffer.clear()
        except Exception as err:
            mesg = "Flush operation error:  " + str(err)
            raise BFDInsightsFirehoseException(mesg)
        finally:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()

            self.release()

    def service_health_check(self):
        # Check for delivery stream in list as a health check.
        response = self.__firehose.list_delivery_streams()

        if self.__delivery_stream_name not in response['DeliveryStreamNames']:
            raise BFDInsightsFirehoseException("Delivery stream name not found for: " + self.__delivery_stream_name)

        return True
