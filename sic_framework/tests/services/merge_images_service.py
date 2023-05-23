import numpy as np
from sic_framework import SICComponentManager, SICService
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor, BottomNaoCameraSensor


class MergeImagesService(SICService):
    def __init__(self, *args, **kwargs):
        super(MergeImagesService, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage, CompressedImageMessage]

    @staticmethod
    def get_output():
        return CompressedImageMessage

    def execute(self, inputs):
        img_a = inputs.get(CompressedImageMessage, TopNaoCameraSensor).image
        img_b = inputs.get(CompressedImageMessage, BottomNaoCameraSensor).image
        out = np.hstack((img_a, img_b))
        return CompressedImageMessage(image=out)

class MergeImages(SICConnector):
    component_class = MergeImagesService


if __name__ == "__main__":
    # from threading import Thread
    # thread = Thread(target=SICFactory, args=(WrapperService, "xps15"))
    # thread.start()
    SICComponentManager([MergeImagesService])
