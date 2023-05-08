from abc import abstractmethod

from sic_framework.core.component_python2 import SICComponent
from .message_python2 import SICMessage


class SICActuator(SICComponent):
    """
    Actuators are components that do not send messages.
    """

    @abstractmethod
    def execute(self, input):
        """
        Main function of the device. Must return a SICMessage as a reply to the user.
        :param input: input messages
        :type input: SICRequest
        :rtype: SICMessage
        """
        return NotImplementedError("You need to define device execution.")

    def on_request(self, request):
        reply = self.execute(request)
        return reply


