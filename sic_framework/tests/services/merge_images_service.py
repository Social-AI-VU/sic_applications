import numpy as np
from sic_framework import SICComponentManager, SICService
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage, SICConfMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoqiCameraSensor, BottomNaoqiCameraSensor

class MergeImageConf(SICConfMessage):
    """
    Configure how to handle duplicate input type based on source component.


    Example usage:

        camera1 = TopNaoCamera(ip="192.168.0.180")
        camera2 = BottomNaoCamera(ip="192.168.0.180")

        conf = MergeImageConf(TopNaoCamera, BottomNaoCamera)
        merger = MergeImages(conf=conf)

        merger.connect(camera1)
        merger.connect(camera2)

    """
    def __init__(self, source_a, source_b):
        super(SICConfMessage, self).__init__()
        self.source_a = source_a
        self.source_b = source_b

class MergeImagesService(SICService):
    def __init__(self, *args, **kwargs):
        super(MergeImagesService, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage, CompressedImageMessage]

    @staticmethod
    def get_output():
        return CompressedImageMessage

    def get_conf(self):
        return MergeImageConf()

    def execute(self, inputs):

        img_a = inputs.get(CompressedImageMessage, self.params.source_a).image
        img_b = inputs.get(CompressedImageMessage, self.params.source_b).image
        out = np.vstack((img_a, img_b))
        return CompressedImageMessage(image=out)

class MergeImages(SICConnector):
    component_class = MergeImagesService


if __name__ == "__main__":
    # from threading import Thread
    # thread = Thread(target=SICFactory, args=(WrapperService, "xps15"))
    # thread.start()
    SICComponentManager([MergeImagesService])
