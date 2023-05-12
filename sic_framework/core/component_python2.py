import threading
import time
from abc import ABCMeta, abstractmethod

import six

import sic_framework.core.sic_logging
from sic_framework.core.utils import isinstance_pickle
from . import sic_logging, utils
from .message_python2 import SICConfMessage, SICRequest, SICMessage, SICSuccessMessage, \
    SICControlRequest, SICPingRequest, SICPongMessage
from .sic_redis import SICRedis


class ConnectRequest(SICRequest):
    def __init__(self, channel):
        """
        A request for this component to start listening to the output of another component. The provided channel should
        be the output channel of the component that serves as input to this component.
        :param channel: the channel
        """
        super(ConnectRequest, self).__init__()
        self.channel = channel  # str


class SICComponent:
    """
    Abstract class for services that provides functions for the Social Interaction Cloud.
    """
    __metaclass__ = ABCMeta

    # This parameter controls how long a SICConnector should wait when requesting the service
    # For example, when the robot has to stand up or model parameters need to load to GPU this might be set higher
    COMPONENT_STARTUP_TIMEOUT = 2

    def __init__(self, ready_event=None, stop_event=None, log_level=sic_logging.INFO, conf=None):
        self._ip = utils.get_ip_adress()

        # the events to control this service running in the thread created by the factory
        self._ready_event = ready_event if ready_event else threading.Event()
        self._stop_event = stop_event if stop_event else threading.Event()

        self._input_channels = []
        self._output_channel = self.get_output_channel(self._ip)

        self.params = None

        # Redis initialization
        self._redis = SICRedis(client_name=self.get_component_name())

        # load config if set by user
        self.set_config(conf)

        self.logger = self._get_logger(log_level)

    def _get_logger(self, log_level):
        """
        Create a logger for the component to use to send messages to the user during its lifetime.
        :param log_level: The logging verbosity level, such as sic_logging.SIC_DEBUG_FRAMEWORK.
        :return: Logger
        """
        # create logger for the component
        name = self.get_component_name()
        return sic_logging.get_sic_logger(self._redis, name, log_level)

    def _start(self):
        """
        Wrapper for actual user implemented start to enable logging to the user.
        """
        try:
            self.start()
        except Exception as e:
            self.logger.exception(e)
            raise e

    def start(self):
        """
        Start the service. Should be called by overriding functions to communicate the service
        has started successfully.
        """
        # register a request handler to handle control requests, e.g. ConnectRequest
        self._redis.register_request_handler(self.get_request_reply_channel(self._ip), self._handle_request)

        # communicate the service is set up and listening to its inputs
        self._ready_event.set()

        self.logger.info("Started component {}".format(self.get_component_name()))

    def _connect(self, connection_request):
        """
        Connect the output of a component to the input of this component, by registering the output channel
        to the on_message handler.
        :param connection_request: The component serving as an input to this component.
        :type connection_request: ConnectRequest
        :return:
        """
        channel = connection_request.channel
        self._redis.register_message_handler(channel, self._handle_message)

    def _handle_message(self, message):
        try:
            return self.on_message(message)
        except Exception as e:
            self.logger.exception(e)
            raise e

    def _handle_request(self, request):
        """
        An handler for control requests such as ConnectRequest. Normal Requests are passed to the on_request handler.
        Also logs the error to the remote log stream in case an exeption occured in the user-defined handler.
        :param request: 
        :return: 
        """

        self.logger.debug_framework_verbose("Handling request {}".format(request.get_message_name()))

        if isinstance_pickle(request, SICPingRequest):
            return SICPongMessage()

        # if isinstance_pickle(request, SICStopRequest):
        #     self._stop_event.set()
        #     return SICSuccessMessage()

        if isinstance_pickle(request, ConnectRequest):
            self._connect(request)
            return SICSuccessMessage()

        if not isinstance_pickle(request, SICControlRequest):
            try:
                return self.on_request(request)
            except Exception as e:
                self.logger.exception(e)
                raise e

        raise TypeError("Unknown request type {}".format(type(request)))

    @classmethod
    def get_component_name(cls):
        """
        The display name of this component.
        """
        return cls.__name__

    @classmethod
    def get_output_channel(cls, ip):
        """
        Get the output channel for this component.
        TODO what place is best to put this method
        TODO maybe explain why this is deterministic?
        :return: channel name
        :rtype: str
        """
        return "{name}:{ip}".format(name=cls.get_component_name(), ip=ip)

    @classmethod
    def get_request_reply_channel(cls, ip):
        """
        Get the channel name to communicate with request-replies with this component
        :return: channel name
        :rtype: str
        """

        name = cls.get_component_name()
        return "{name}:reqreply:{ip}".format(name=name, ip=ip)

    def set_config(self, new=None):
        # Service parameter configuration
        if new:
            conf = new
        else:
            conf = self.get_conf()

        self._parse_conf(conf)

    def on_request(self, request):
        """
        Define the handler for requests. Must return a SICMessage as a reply to the request.
        :param request: The request for this component.
        :return: The reply
        :rtype: SICMessage
        """
        raise NotImplementedError("You need to define a request handler.")


    def on_message(self, message):
        """
        Define the handler for input messages.
        :param message: The request for this component.
        :return: The reply
        :rtype: SICMessage
        """
        raise NotImplementedError("You need to define a message handler.")

    @staticmethod
    @abstractmethod
    def get_inputs():
        """
        Define the inputs the service needs as a list
        :return: list of SIC messages
        :rtype: List[Type[SICMessage]]
        """
        raise NotImplementedError("You need to define service input.")

    @staticmethod
    @abstractmethod
    def get_output():
        """
        Define the output of the service
        :return: SIC message
        :rtype: Type[SICMessage]
        """
        raise NotImplementedError("You need to define service output.")

    @staticmethod
    def get_conf():
        """
        Define a possible configuration using SICConfMessage
        :return: a SICConfMessage or None
        :rtype: SICConfMessage
        """
        return SICConfMessage()

    def _parse_conf(self, conf):
        """
        Helper function to parse configuration messages (SICConfMessage)
        :param conf: a SICConfMessage with the parameters as fields
        :type conf: SICConfMessage
        """
        assert isinstance_pickle(conf, SICConfMessage), "Configuration message should be of type SICConfMessage, " \
                                                        "is {type_conf}".format(type_conf=type(conf))

        if conf == self.params:
            self.logger.info("New configuration is identical to current configuration.")
            return

        self.params = conf

    def _get_timestamp(self):
        # TODO this needs to be synchronized with all devices, because if a nao is off by a second or two
        # its data will align wrong with other sources
        return time.time()

    def stop(self, *args):
        self.logger.debug('Trying to exit {} gracefully...'.format(self.get_component_name()))
        try:
            # TODO unregister all listeners
            self._redis.close()
            self._stop_event.set()
            self.logger.debug('Graceful exit was successful')
        except Exception as err:
            self.logger.error('Graceful exit has failed: {}'.format(err.message))
