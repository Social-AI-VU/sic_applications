from __future__ import print_function

import io
import logging

from . import utils
from .message_python2 import SICMessage
from .sic_redis import SICRedis


def get_log_channel():
    """
    Get the global log channel. All components on any device should log to this channel.
    """
    return "sic:logging"


class SICLogMessage(SICMessage):
    def __init__(self, msg):
        """
        A wrapper for log messages to be sent over the SICRedis pubsub framework.
        :param msg: The log message to send to the user
        """
        self.msg = msg
        super(SICLogMessage, self).__init__()

class SICRemoteError(Exception):
    """An exception indicating the error happend on a remote device"""

class SICLogSubscriber(object):

    def __init__(self):
        self.redis = None
        self.started = False

    def subscribe_to_log_channel_once(self):
        """
        Subscribe to the log channel and display any messages on the terminal to propagate any log messages in the
        framework tot the user. This function may be called multiple times but will only subscribe once.
        :return:
        """

        if not self.started:
            self.redis = SICRedis(client_name="SICLogSubscriber")
            self.redis.register_message_handler(get_log_channel(), self._handle_log_message)
            self.started = True


    def _handle_log_message(self, message):
        """
        Handle a message sent on a debug stream. Currently its just printed to the terminal.
        :param message: SICLogMessage
        """
        print(message.msg, end="")

        if "ERROR" in message.msg.split(":")[1]:
            raise SICRemoteError("Error occurred, see remote stacktrace above.")

# pseudo singleton object. Does nothing when this file is executed during the import, but can subscribe to the log
# channel for the user with subscribe_to_log_channel_once
SIC_LOG_SUBSCRIBER = SICLogSubscriber()

class SICLogStream(io.TextIOBase):
    """
    Facilities to log to redis as a file-like object, to integrate with standard python
    logging facilities.
    """

    def __init__(self, redis, logging_channel):
        self.redis = redis
        self.logging_channel = logging_channel

    def readable(self):
        return False

    def writable(self):
        return True

    def write(self, msg):
        message = SICLogMessage(msg)
        self.redis.send_message(self.logging_channel, message)

    def flush(self):
        return


class SICLogFormatter(logging.Formatter):

    def formatException(self, exec_info):
        """
        Prepend every exption with a | to indicate it is not local.
        :param exec_info:
        :return:
        """
        text = super(SICLogFormatter, self).formatException(exec_info)
        text = "| " + text.replace("\n", "\n| ")
        text += "\n| NOTE: Exception occurred in SIC framework, not application"
        return text


def get_sic_logger(redis, name, log_level):
    """
    Set up logging to the log output channel to be able to report messages to users. Also logs to the terminal.

    :param redis: The SICRedis object
    :param name: A readable and identifiable name to indicate to the user where the log originated
    :param log_level: The logger.LOGLEVEL verbosity level
    :param log_messages_channel: the output channel of this service, on which the log output channel is based.
    """
    # logging initialisation
    logger = logging.Logger(name)
    logger.setLevel(log_level)

    debug_stream = SICLogStream(redis, get_log_channel())
    handler_redis = logging.StreamHandler(debug_stream)

    log_format = SICLogFormatter('[%(name)s {ip}]: %(levelname)s: %(message)s'.format(ip=utils.get_ip_adress()))
    handler_redis.setFormatter(log_format)

    handler_terminal = logging.StreamHandler()
    handler_terminal.setFormatter(log_format)

    logger.addHandler(handler_redis)
    logger.addHandler(handler_terminal)

    return logger


# Loglevel interpretation
# mostly follows python's defaults

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20  # service dependent sparse information
DEBUG = 10   # service dependent verbose information
SIC_DEBUG_FRAMEWORK = 6  # sparse messages, e.g. when executing, etc.
SIC_DEBUG_FRAMEWORK_VERBOSE = 4  # detailed messages, e.g. for each input output operation
NOTSET = 0

def debug_framework(self, message, *args, **kws):
    if self.isEnabledFor(SIC_DEBUG_FRAMEWORK):
        # Yes, logger takes its '*args' as 'args'.
        self._log(SIC_DEBUG_FRAMEWORK, message, args, **kws)

def debug_framework_verbose(self, message, *args, **kws):
    if self.isEnabledFor(SIC_DEBUG_FRAMEWORK_VERBOSE):
        # Yes, logger takes its '*args' as 'args'.
        self._log(SIC_DEBUG_FRAMEWORK_VERBOSE, message, args, **kws)


logging.addLevelName(SIC_DEBUG_FRAMEWORK, "SIC_DEBUG_FRAMEWORK")
logging.addLevelName(SIC_DEBUG_FRAMEWORK_VERBOSE, "SIC_DEBUG_FRAMEWORK_VERBOSE")

logging.Logger.debug_framework = debug_framework
logging.Logger.debug_framework_verbose = debug_framework_verbose


