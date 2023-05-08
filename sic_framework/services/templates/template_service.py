from sic_framework.devices.common_naoqi.naoqi_camera import DepthImageMessage, StereoImageMessage
from sic_framework import SICComponentManager, SICService, SICConfMessage


class ExampleService(SICService):
    def __init__(self, *args, **kwargs):
        super(ExampleService, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [StereoImageMessage]

    @staticmethod
    def get_output():
        return DepthImageMessage

    # This function is optional
    @staticmethod
    def get_conf():
        return SICConfMessage()

    def execute(self, inputs):
        # Do something, this is the core of your service
        return DepthImageMessage()


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device (id: local)
    SICComponentManager([ExampleService], "local")
