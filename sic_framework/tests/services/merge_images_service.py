import numpy as np
from sic_framework import SICComponentManager, SICService
from sic_framework.core.message_python2 import CompressedImageMessage


class MergeImages(SICService):
    def __init__(self, *args, **kwargs):
        super(MergeImages, self).__init__(*args, **kwargs)

    @staticmethod
    def get_inputs():
        return [CompressedImageMessage, CompressedImageMessage]

    @staticmethod
    def get_output():
        return CompressedImageMessage

    def execute(self, inputs):
        img_a = inputs[CompressedImageMessage.id(index=0)].image
        img_b = inputs[CompressedImageMessage.id(index=1)].image
        out = np.hstack((img_a, img_b))
        return CompressedImageMessage(image=out)


if __name__ == "__main__":
    # from threading import Thread
    # thread = Thread(target=SICFactory, args=(WrapperService, "xps15"))
    # thread.start()

    SICComponentManager([MergeImages], "xps15")
