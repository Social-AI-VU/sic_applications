import collections
from abc import ABCMeta, abstractmethod
from threading import Event

from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.utils import is_sic_instance

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
        # TODO when inputs arrive faster than processing, the buffer might fill up. Do we want to handle this better or
        # just silence the logging. Maybe its better to log only when receiving lots of messages but never executing.

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
    A dictionary type container for messages, indexable by the message type and possibly an origin.

    Example:
        # in config: self.params.image_source_one = TopCameraSensor
        img_msg1 = inputs.get(ImageMessage, self.params.image_source_one)
        img_msg2 = inputs.get(ImageMessage, self.params.image_source_two)

        audio_msg = inputs.get(AudioMessage)
    """

    def __init__(self):
        self.messages = collections.defaultdict(lambda: list())

    def set(self, message):
        self.messages[message.get_message_name()].append(message)

    def get(self, type, source_component=None):

        if source_component is not None:
            try:
                source_component_name = source_component.get_component_name()
            except AttributeError:
                # Object is SICConnector and not SICComponent
                source_component_name = source_component.component_class.get_component_name()

        messages = self.messages[type.get_message_name()]

        assert len(messages), "Attempting to get message from empty buffer (framework issue, should not be possible)"

        for message in messages:
            if source_component is not None:
                # find the message with the right source component in the list of duplicate input types
                if message._previous_component_name == source_component_name:
                    return message
            else:
                # if no source component is set, just accept any (should be only 1)
                return message

        raise IndexError("Input of type {} with source: {} not found.".format(type, source_component))


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

        self._input_buffers = dict()

    def start(self):
        """
        Start the service. This method must be called by the user at the end of the constructor
        """
        super(SICService, self).start()

        self._listen()

    @abstractmethod
    def execute(self, inputs):
        """
        Main function of the service
        :param inputs: dict of input messages from other components
        :type inputs: SICMessageDictionary
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

        # Buffers are created dynamically, based on the source components. Only start executing once
        # we have at least one buffer per message type
        if len(self._input_buffers) != len(self.get_inputs()):
            raise PopMessageException("Not enough buffer has been created yet")

        # Second, we go through each buffer and check if we can find a message that is within the time difference
        # threshold. Duplicate input types are in separate buffers based on their _previous_component attribute.


        # TODO might raise
        # RuntimeError: deque mutated during iteration
        # in for msg in buffer: as on_message could be set while iterating
        message_dict = SICMessageDictionary()
        messages_to_remove = []
        for name, buffer in self._input_buffers.items():
            # get the newest message in the buffer closest to the selected timestamp
            # if there is none, we raise a ValueError to stop searching and wait for new data again
            for msg in buffer:
                if abs(msg._timestamp - selected_timestamp) <= self.MAX_MESSAGE_AGE_DIFF_IN_SECONDS:

                    message_dict.set(msg)
                    messages_to_remove.append(msg)
                    break
            else:
                # the timestamps across all buffers did not align within the threshold, so do not pop messages
                raise PopMessageException("Could not collect aligned input data from buffers, no matching timestamps")

        # Third, we now know all buffers contain a valid (aligned) message for the timestamp
        # only then, consume these messages from the buffers and return the messages.
        for buffer, msg in zip(self._input_buffers.values(), messages_to_remove):
            buffer.remove(msg)

        return message_dict, selected_timestamp

    def on_message(self, message):
        """
        Collect an input message into the appropriate buffer.
        :param data: the redis pubsub message
        """

        # TODO support inheritance by indexing using the superclass that matches an input type
        # for b in msg.__class__.__mro__:
        #     if issubclass(b, SICMessage):

        idx = (message.get_message_name(), message._previous_component_name)

        try:
            self._input_buffers[idx].appendleft(message)
        except KeyError:
            self._input_buffers[idx] = MessageQueue(self.logger)
            self._input_buffers[idx].appendleft(message)

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

                self.output_message(output)

        self.logger.debug("Stopped listening")
        self.stop()
