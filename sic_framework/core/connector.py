import logging
import time
from abc import ABCMeta

import six

from sic_framework.core.component_python2 import ConnectRequest
from sic_framework.core.sensor_python2 import SICSensor
from sic_framework.core.utils import is_sic_instance
from . import utils
from .component_manager_python2 import SICStartComponentRequest, SICNotStartedMessage
from .message_python2 import SICMessage, SICRequest, SICStopRequest, SICPingRequest
from .sic_logging import SIC_LOG_SUBSCRIBER
from .sic_redis import SICRedis


class ComponentNotStartedError(Exception):
    pass


class SICConnector(object):
    __metaclass__ = ABCMeta

    # define how long an "instant" reply should take at most (ping sometimes takes more than 150ms)
    _PING_TIMEOUT = 1

    def __init__(self, ip="localhost", log_level=logging.INFO, conf=None):
        """
        A proxy that enables communication with a component that has been started. We can send messages to, and receive
        from the component that is running on potentially another computer.
        
        :param ip: the ip adress of the device the service is running on
        :param log_level: Controls the verbosity of the connected component logging.
        :param conf: Optional SICConfMessage to set component parameters.
        """
        self._redis = SICRedis()

        assert isinstance(ip, str), "IP must be string"

        # default ip adress is local ip adress (the actual inet, not localhost or 127.0.0.1)

        if ip in ["localhost", "127.0.0.1"]:
            ip = utils.get_ip_adress()

        self._ip = ip

        self._callback_threads = []

        self._request_reply_channel = self.component_class.get_request_reply_channel(ip)
        self._log_level = log_level
        self._conf = conf

        # Subscribe to the log channel to display to the user
        SIC_LOG_SUBSCRIBER.subscribe_to_log_channel_once()

        self.output_channel = self.component_class.get_output_channel(self._ip)

        # if we cannot ping the component, request it to be started from the ComponentManager
        if not self._ping():
            self._start_component()

        # subscribe the component to a channel that the user is able send a message on if needed
        self.input_channel = "{}:input:{}".format(self.component_class.get_component_name(), self._ip)
        self.request(ConnectRequest(self.input_channel), timeout=self._PING_TIMEOUT)

    def _ping(self):
        try:
            self.request(SICPingRequest(), timeout=self._PING_TIMEOUT)
            return True

        except TimeoutError:
            return False

    @property
    def component_class(self):
        """
        This abstract property should be set by the subclass creating a connector for the specific component.
        e.g.
        component_class = NaoCamera
        """
        raise NotImplementedError("Abstract member component_class not set.")

    def _start_component(self):
        """
        Request the component to be started. This connector provides the input and output channels, as it determines which
        components is connected to which other components.
        log_level allows the user to control the verbosity of the connected component.

        :param component: The component we request to be started
        :param device_id: The id of the device we wat to start a component on

        """
        print("Component not already alive, requesting", self.component_class.get_component_name(), "from manager ", self._ip)

        if issubclass(self.component_class, SICSensor) and self._conf:
            print("Warning: setting configuration for SICSensors only works the first time connecting (sensor "
                  "component instances are reused for now)")

        component_request = SICStartComponentRequest(
            component_name=self.component_class.get_component_name(),
            log_level=self._log_level,
            conf=self._conf)

        # factory returns a SICStartedComponentInformation

        try:

            component_info = self._redis.request(self._ip, component_request,
                                                 timeout=self.component_class.COMPONENT_STARTUP_TIMEOUT)
            if is_sic_instance(component_info, SICNotStartedMessage):

                raise ComponentNotStartedError(
                    "\n\nComponent did not start, error should be logged above. ({})".format(component_info.message))

        except TimeoutError as e:
            six.raise_from(TimeoutError("Could not connect to component. Is SIC running on the device (ip:{})?".format(self._ip)), None)


    def register_callback(self, callback):
        """
        Subscribe a callback to be called when there is new data available.
        :param callback: the function to execute.
        """

        ct = self._redis.register_message_handler(self.output_channel, callback)

        self._callback_threads.append(ct)

    def send_message(self, message):
        # Update the timestamp, as it should be set by the device of origin
        message._timestamp = self._get_timestamp()
        self._redis.send_message(self.input_channel, message)

    def _get_timestamp(self):
        # TODO this needs to be synchronized with all devices, because if a nao is off by a second or two
        # its data will align wrong with other sources
        # possible solution: do redis.time, and use a custom get time functions that is aware of the offset
        return time.time()

    def connect(self, component):
        """
        Connect the output of a component to the input of this component.
        :param component: The component connector providing the input to this component
        :type component: SICConnector
        :return:
        """

        assert isinstance(component, SICConnector), "Component connector is not a SICConnector " \
                                                    "(type:{})".format(type(component))

        request = ConnectRequest(component.output_channel)
        self._redis.request(self._request_reply_channel, request)

    def request(self, request, timeout=100.0, block=True):
        """
        Request data from a device. Waits until the reply is received. If the reply takes longer than
        `timeout` seconds to arrive, a TimeoutError is raised. If block is set to false, the reply is
        ignored and the function returns immediately.
        :param request: The request to the device
        :type request: SICRequest
        :param timeout: A timeout in case the action takes too long. Only works when blocking=True.
        :param block: If false, immediately returns None after sending the request.
        :return: the SICMessage reply from the device, or none if blocking=False
        :rtype: SICMessage | None
        """
        assert utils.is_sic_instance(request, SICRequest), "Cannot send requests that do not inherit from " \
                                                             "SICRequest (type: {req})".format(req=type(request))

        # Update the timestamp, as it is not yet set (normally be set by the device of origin, e.g a camera)
        request._timestamp = self._get_timestamp()

        return self._redis.request(self._request_reply_channel, request, timeout=timeout, block=block)

    def stop(self):
        """
        Stop the component and disconnect the callback.
        """
        # self._redis.send_message(self._request_reply_channel, SICStopRequest())
        print("Cleanup")
        for ct in self._callback_threads:
            self._redis.unregister_callback(ct)

        self._redis.close()

    # TODO: maybe put this in constructor to do a graceful exit on crash?
    # register cleanup to disconnect redis if an exception occurs anywhere during exection
    # TODO FIX cannot register multiple exepthooks
    # sys.excepthook = self.cleanup_after_except
    # #
    # def cleanup_after_except(self, *args):
    #     self.stop()
    #     # call original except hook after stopping
    #     sys.__excepthook__(*args)

    # TODO: maybe also helps for a graceful exit?
    def __del__(self):
        self.stop()
