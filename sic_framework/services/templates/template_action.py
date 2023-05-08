from sic_framework import SICComponentManager, SICActuator, SICConfMessage, SICRequest, SICMessage


class DummyConf(SICConfMessage):
    """
    Dummy SICConfMessage
    """
    def __init__(self):
        super(SICConfMessage, self).__init__()


class DummyRequest(SICRequest):
    """
    Dummy SICRequest
    """
    def __init__(self):
        super(SICRequest, self).__init__()


class DummyResult(SICMessage):
    """
    Dummy result object
    """
    def __init__(self):
        super(SICMessage, self).__init__()


class ExampleActuator(SICActuator):
    """
    Dummy SICAction
    """
    def __init__(self, *args, **kwargs):
        super(ExampleActuator, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [DummyRequest]

    @staticmethod
    def get_output():
        return DummyResult

    # This function is optional
    @staticmethod
    def get_conf():
        return DummyConf()

    def execute(self, input):
        # Do something, this is the core of your service
        return DummyResult()


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device (id: local)
    SICComponentManager([ExampleActuator], "local")
