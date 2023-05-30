from sic_framework import SICComponentManager, SICConfMessage
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import BoundingBox, BoundingBoxesMessage, CompressedImageMessage


class DummyConf(SICConfMessage):
    """
    Dummy SICConfMessage
    """

    def __init__(self, my_parameter=123.456):
        super(SICConfMessage, self).__init__()
        self.my_parameter = my_parameter


class ExampleComponent(SICComponent):
    """
    Dummy SICAction
    """

    def __init__(self, *args, **kwargs):
        super(ExampleComponent, self).__init__(*args, **kwargs)
        # Do component initialization

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage]

    @staticmethod
    def get_output():
        return BoundingBoxesMessage

    # This function is optional
    @staticmethod
    def get_conf():
        return DummyConf()

    def do_my_detection(self, image):
        """
        Pseudo-code example method
        :param image: np.array
        :return: BoundingBoxesMessage
        """
        objects = my_detection_system(image, parameter=self.params.my_parameter)

        bboxes = [BoundingBox(*obj.to_list()) for obj in objects]
        return BoundingBoxesMessage(bboxes)

    def on_message(self, message):
        # Do something, this is the core of your service
        # Pseudocode example:
        output = self.do_my_detection(message.image)

        self.output_message(output)

    def on_request(self, request):
        # Do something, this is the core of your service
        # Pseudocode example:
        output = self.do_my_detection(request.image)

        return output


class Example(SICConnector):
    component_class = ExampleComponent


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device
    SICComponentManager([ExampleComponent])
