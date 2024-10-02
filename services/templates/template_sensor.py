from sic_framework import SICComponentManager, SICConfMessage, SICMessage, SICSensor
from sic_framework.core.connector import SICConnector


class ExampleConf(SICConfMessage):
    """
    Dummy SICConfMessage
    """

    def __init__(self, my_parameter=123.456):
        super(SICConfMessage, self).__init__()
        self.my_parameter = my_parameter


class ExampleMessage(SICMessage):
    """
    Dummy custom output message type.
    """

    def __init__(self, example_data):
        self.example_data = example_data


class ExampleService(SICSensor):
    def __init__(self, *args, **kwargs):
        super(ExampleService, self).__init__(*args, **kwargs)
        # Set up your sensor

        # Pseudo-code example:
        parameter = self.params.my_parameter
        self.sensor = do_sensor_setup(parameter=parameter)

    @staticmethod
    def get_output():
        return ExampleMessage

    # This function is optional
    @staticmethod
    def get_conf():
        return SICConfMessage()

    def execute(self):
        # Do something, this is the core of your service
        # Pseudo-code example:
        example_data = self.sensor.read_sensor_values()

        return ExampleMessage(example_data)


class Example(SICConnector):
    component_class = ExampleService


if __name__ == '__main__':
    SICComponentManager([ExampleService])
