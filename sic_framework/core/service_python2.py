import collections
from abc import ABCMeta, abstractmethod
from threading import Event

from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.utils import isinstance_pickle

from . import sic_logging
from .message_python2 import SICMessage, SICConfMessage


class MessageQueue(collections.deque):
    def __init__(self, logger):
        """
        A message buffer, with logging to notify of excessive dropped messages.
        """
        self.logger = logger
        self.dropped_messages_counter = 0
        super(MessageQueue, self).__init__(maxlen=SICService.MAX_MESSAGE_BUFFER_SIZE)

    def appendleft(self, x):
        if len(self) == self.maxlen:
            self.dropped_messages_counter += 1
            if self.dropped_messages_counter in {5, 10, 50, 100, 200, 1000, 5000, 10000}:
                self.logger.warning("Dropped {} messages of type {}".format(self.dropped_messages_counter,
                                                                            x.get_message_name()))
        return super(MessageQueue, self).appendleft(x)


class PopMessageException(ValueError):
    """
    An exception to raise whenever the conditions to pop messages from the input message buffers were not met.
    """


class SICMessageDictionary:
    """
    TODO
    """

    def __init__(self, allowed_classes):
        pass
        self.allowed_classes = {b.id() for b in allowed_classes}
        self.message_class_mapping = collections.OrderedDict()
        self.input_type_count = collections.defaultdict(lambda: 0)

    def set(self, msg):
        for b in msg.__class__.__mro__:
            if issubclass(b, SICMessage) and b.id() in self.allowed_classes:
                count = self.input_type_count[b.id()]
                self.message_class_mapping[b.id(index=count)] = msg
                self.input_type_count[b.id()] += 1

                break


class SICService(SICComponent):
    """
    Abstract class for services that provides data fusion based on the timestamp of the data origin.
    """

    MAX_MESSAGE_BUFFER_SIZE = 10
    MAX_MESSAGE_AGE_DIFF_IN_SECONDS = .5  # TODO tune? maybe in config? Can be use case dependent

    def __init__(self, *args, **kwargs):
        super(SICService, self).__init__(*args, **kwargs)

        # this event is set whenever a new message arrives.
        self._new_data_event = Event()


        # TODO this does not handle duplicate input type
        # A solution is to add a parameter to all messages with the component name that outputed it last
        # this can be appended to the message name, which would lead to separate buffers.
        # a conf can be set to handle which component leads to which "index"
        self._input_buffers = collections.OrderedDict()
        for input_type in self.get_inputs():
            self._input_buffers[input_type.get_message_name()] = MessageQueue(self.logger)

    def start(self):
        """
        Start the service. This method must be called by the user at the end of the constructor
        """
        super(SICService, self).start()

        self.logger.info('Starting {}'.format(self.get_component_name()))

        self._listen()

    @abstractmethod
    def execute(self, inputs):
        """
        Main function of the service
        :param inputs: dict of input messages from other components
        :type inputs: dict[str, SICMessage]
        :return: A SICMessage or None
        :rtype: SICMessage | None
        """
        raise NotImplementedError("You need to define service execution.")

    def _pop_messages(self):
        """
        Collect all input SICdata messages gathered in the buffers into a dictionary to use in the execute method.
        Make sure all input messages are aligned to the newest timestamp to synchronise the input data.
        If multiple channels contain the same type, give them an index in the service_input dict.

        If the buffers do not contain an aligned set of messages, a PopMessageException is raised.
        :raises: PopMessageException
        :return: tuple of dictionary of messages and the shared timestamp
        """

        self.logger.debug_framework_verbose(
            "input buffers: {}".format([(k, len(v)) for k, v in self._input_buffers.items()]))

        # First, get the most recent message for all buffers. Then, select the oldest message from these messages.
        # The timestamp of this message corresponds to the most recent timestamp for which we have all information
        # available
        try:
            selected_timestamp = min([buffer[0]._timestamp for buffer in self._input_buffers.values()])
        except IndexError:
            # Not all buffers are full, so do not pop messages
            raise PopMessageException("Could not collect aligned input data from buffers, not all buffers filled")

        # Second, we go through each buffer and check if we can find a message that is within the time difference
        # threshold. If there are duplicate input types, their occurrence is counted and registered by index in the
        # service input dict. The order matters for this, so _input_buffers is also an OrderedDict

        message_dict = SICMessageDictionary(self.get_inputs())
        for buffer in self._input_buffers.values():
            # get the newest message in the buffer closest to the selected timestamp
            # if there is none, we raise a ValueError to stop searching and wait for new data again
            for msg in buffer:
                if abs(msg._timestamp - selected_timestamp) <= self.MAX_MESSAGE_AGE_DIFF_IN_SECONDS:
                    message_dict.set(msg)
                    break
            else:
                # the timestamps across all buffers did not align within the threshold, so do not pop messages
                raise PopMessageException("Could not collect aligned input data from buffers, no matching timestamps")

        # The message have been collected according to their (inherited) type
        service_inputs = message_dict.message_class_mapping

        # Third, we now know all buffers contain a valid (aligned) message for the timestamp
        # only then, consume these messages from the buffers and return the messages.
        for buffer, msg in zip(self._input_buffers.values(), service_inputs.values()):
            buffer.remove(msg)

        return service_inputs, selected_timestamp


    def on_message(self, message):
        """
        Collect an input message into the appropriate buffer.
        :param data: the redis pubsub message
        """

        self._input_buffers[message.get_message_name()].appendleft(message)

        self._new_data_event.set()

    def _listen(self):
        """
        Wait for data and execute the service when possible.
        """
        while not self._stop_event.is_set():
            # wait for new data to be set by the _process_message callback, and check every .1 second to check if the
            # service must stop
            self._new_data_event.wait(timeout=.1)

            if not self._new_data_event.is_set():
                continue

            # clear the flag so we will wait for new data again next iteration
            self._new_data_event.clear()

            # pop messages if all buffers contain a timestamp aligned message, if not a PopMessageException is raised
            # and we will have to wait for new data
            try:
                messages, timestamp = self._pop_messages()
            except PopMessageException:
                self.logger.debug_framework_verbose("Did not pop messages from buffers.")
                continue

            output = self.execute(messages)

            self.logger.debug_framework_verbose("Outputting message {}".format(output))

            if output:
                # To keep track of the creation time of this data, the output timestamp is the oldest timestamp of all
                # the timestamp sources.
                output._timestamp = timestamp

                self._redis.send_message(self._output_channel, output)

        self.logger.debug("Stopped listening")
        self.stop()
