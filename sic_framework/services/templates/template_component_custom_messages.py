from sic_framework import SICComponentManager, SICConfMessage, SICRequest, SICMessage
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector


class DummyConf(SICConfMessage):
    """
    Dummy SICConfMessage
    """

    def __init__(self):
        super(SICConfMessage, self).__init__()


class DummyRequest(SICRequest):
    """
    Dummy request
    """

    def __init__(self):
        super(SICRequest, self).__init__()


class DummyMessage(SICMessage):
    """
    Dummy input message
    """

    def __init__(self):
        super(SICMessage, self).__init__()


class DummyOutputMessage(SICMessage):
    """
    Dummy input message
    """

    def __init__(self):
        super(SICMessage, self).__init__()


class ExampleComponent(SICComponent):
    """
    Dummy SICAction
    """

    def __init__(self, *args, **kwargs):
        super(ExampleComponent, self).__init__(*args, **kwargs)
        # Do component initialization

    @staticmethod
    def get_inputs():
        return [DummyRequest]

    @staticmethod
    def get_output():
        return DummyOutputMessage

    # This function is optional
    @staticmethod
    def get_conf():
        return DummyConf()

    def on_message(self, message):
        # Do something, this is the core of your service
        result = DummyOutputMessage()
        self.output_message(result)

    def on_request(self, request):
        # Do something, this is the core of your service
        return DummyOutputMessage()


class Example(SICConnector):
    component_class = ExampleComponent


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device
    SICComponentManager([ExampleComponent])
