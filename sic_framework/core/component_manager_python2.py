import copy
import threading
import time
from signal import signal, SIGTERM, SIGINT
from sys import exit

import sic_framework.core.sic_logging
from sic_framework.core.utils import is_sic_instance

from . import utils, sic_logging
from .message_python2 import SICMessage, SICStopRequest, SICRequest, SICIgnoreRequestMessage, SICSuccessMessage
from .sic_redis import SICRedis


class SICStartComponentRequest(SICRequest):
    """
    A request from a user for this component manager, running on a device, to start a component which
    will be providing some type of capability from this device.
    """

    def __init__(self, component_name, log_level, conf=None):
        super(SICStartComponentRequest, self).__init__()
        self.component_name = component_name  # str
        self.log_level = log_level  # logging.LOGLEVEL
        self.conf = conf  # SICConfMessage


class SICNotStartedMessage(SICMessage):
    def __init__(self, message):
        self.message = message


class SICComponentManager(object):
    # The maximum error between the redis server and this device's clocks in seconds
    MAX_REDIS_SERVER_TIME_DIFFERENCE = 2

    # Number of seconds we wait at most for a component to start
    COMPONENT_START_TIMEOUT = 10

    def __init__(self, component_classes):
        """
        A component manager to start components when requested by users.
        :param component_classes: List of SICService components to be started
        """

        # Redis initialization
        self.redis = SICRedis()
        self.ip = utils.get_ip_adress()

        self.active_components = []
        self.component_classes = {cls.get_component_name(): cls for cls in component_classes}
        self.component_counter = 0

        self.stop_event = threading.Event()
        self.ready_event = threading.Event()

        self.logger = self.get_manager_logger()
        self.redis.parent_logger = self.logger

        # The _handle_request function is calls execute directly, as we must reply when execution done to allow the user
        # to wait for this. New messages will be buffered by redis. The component manager listens to
        self.redis.register_request_handler(self.ip, self._handle_request)

        self.logger.info('Starting component manager on ip "{}" with components:'.format(self.ip))
        for c in self.component_classes.values():
            self.logger.info(" - {}".format(c.get_component_name()))

        # TODO FIXME
        # self._sync_time()

        self.ready_event.set()
        self.serve()

    def serve(self):
        """
        Listen for requests until this component manager is signaled to stop running.
        """
        # wait for the signal to stop, loop is necessary for ctrl-c to work on python2
        try:
            while True:
                self.stop_event.wait(timeout=.1)
                if self.stop_event.is_set():
                    break
        except KeyboardInterrupt:
            pass

        self.shutdown()
        print("Stopped component manager.")

    def _sync_time(self):
        """
        WORK IN PROGRESS: Does not work!
        clock on devices is often not correct, so we need to correct for this
        """
        # Check if the time of this device is off, because that would interfere with sensor fusion across devices
        time_diff_seconds = abs(time.time() - float("{}.{}".format(*self.redis.time())))
        if time_diff_seconds > .1:
            print("Warning: device time difference to redis server is {} seconds".format(time_diff_seconds))
            print("This is allowed (max: {}), but might cause data to fused incorrectly in components.".format(
                self.MAX_REDIS_SERVER_TIME_DIFFERENCE))
        if time_diff_seconds > self.MAX_REDIS_SERVER_TIME_DIFFERENCE:
            raise ValueError("The time on this device differs by {} seconds from the redis server (max: {}s)".format(
                time_diff_seconds, self.MAX_REDIS_SERVER_TIME_DIFFERENCE))

    def _handle_request(self, request):
        """
        Start a component on this device as requested by a user. A thread is started to run the component, and component
        threads are restarted/reused when a user re-requests the component. Separated such that SICSingletonFactory can
        override this method.
        :param request: The SICStartServiceRequest request
        """

        if is_sic_instance(request, SICStopRequest):
            self.stop_event.set()
            # return an empty stop message as a request must always be replied to
            return SICSuccessMessage()

        # reply to the request if the component manager can start the component
        if request.component_name in self.component_classes:
            print("{} handling request {}".format(self.__class__.__name__, request.component_name))

            return self.start_component(request)
        else:
            print("{} ignored request {}".format(self.__class__.__name__, request.component_name))
            return SICIgnoreRequestMessage()

    def get_manager_logger(self, log_level=sic_logging.INFO):
        """
        Create a logger to inform the user during the setup of the component by the manager.
        :return: Logger
        """
        name = "{manager}".format(manager=self.__class__.__name__)

        logger = sic_logging.get_sic_logger(self.redis, name, log_level)
        logger.info("Manager on device {} starting".format(self.ip))

        return logger

    def start_component(self, request):
        """
        Start a component on this device as requested by a user. A thread is started to run the component in.
        :param request: The SICStartServiceRequest request
        :param logger: The logger for any messages from the component manager
        :return: the SICStartedServiceInformation with the information to connect to the started component.
        """

        component_class = self.component_classes[request.component_name] # SICComponent

        component = None
        try:
            stop_event = threading.Event()
            ready_event = threading.Event()
            component = component_class(stop_event=stop_event,
                                        ready_event=ready_event,
                                        log_level=request.log_level,
                                        conf=request.conf,
                                        )
            self.active_components.append(component)

            thread = threading.Thread(target=component._start)
            thread.name = component_class.get_component_name()
            thread.start()

            # wait till the component is ready to receive input
            component._ready_event.wait(component.COMPONENT_STARTUP_TIMEOUT)

            if component._ready_event.is_set() is False:
                self.logger.error(
                    "Component {} refused to start within {} seconds!".format(component.get_component_name(), component.COMPONENT_STARTUP_TIMEOUT))
                # Todo do something!

            # inform the user their component has started
            reply = SICSuccessMessage()

            return reply

        except Exception as e:
            self.logger.exception(e) # maybe not needed if already sending back a not started message
            if component is not None:
                component.stop()
            return SICNotStartedMessage(e)

    def shutdown(self, *args):
        print('Trying to exit manager gracefully...')
        try:
            self.redis.close()
            for component in self.active_components:
                component.stop()
                # component._stop_event.set()
            print('Graceful exit was successful')
        except Exception as err:
            print('Graceful exit has failed: {}'.format(err.message))