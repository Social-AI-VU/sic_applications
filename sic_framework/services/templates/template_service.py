from sic_framework import SICComponentManager, SICService, SICConfMessage, SICMessage
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage


class ExampleMessage(SICMessage):
    def __init__(self, example_data):
        self.example_data = example_data


class ExampleService(SICService):
    def __init__(self, *args, **kwargs):
        super(ExampleService, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage]

    @staticmethod
    def get_output():
        return ExampleMessage

    # This function is optional
    @staticmethod
    def get_conf():
        return SICConfMessage()

    def execute(self, inputs):
        image_message = inputs.get(CompressedImageMessage)

        # Do something, this is the core of your service
        example_data = [1, 2, 3]

        return ExampleMessage(example_data)


class Example(SICConnector):
    component_class = ExampleService


if __name__ == '__main__':
    SICComponentManager([ExampleService])
