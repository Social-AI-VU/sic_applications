import logging
import threading
import time

import numpy as np
from sic_framework import SICComponentManager, SICService, SICMessage, sic_logging

# @dataclass
from sic_framework.core.sensor_python2 import SICSensor
from sic_framework.core.sic_redis import SICRedis


class ImgMessage(SICMessage):
    def __init__(self, current_time, image):
        self.current_time = current_time
        self.image = image


class StreamImgService(SICSensor):

    def __init__(self, *args, **kwargs):
        super(StreamImgService, self).__init__(*args, **kwargs)
        self.logger.warning("StreamImgService constructor")
        self.sent = 0
        self.MAX_SEND = 100000
        self.width = 640
        self.height = 480
        self.depth = 3

    @staticmethod
    def get_inputs():
        return []

    @staticmethod
    def get_output():
        return ImgMessage

    def execute(self):

        self.img = (np.random.rand(self.width, self.height, self.depth) * 255).astype(np.uint8)

        if not self.sent:
            self.start_time = time.time()
            print("Streaming", self.sent, self.start_time)

        if (self.sent + 1) == self.MAX_SEND:
            self.end_time = time.time()
            print("MAX STEAMING REACHED", self.sent, self.end_time)
            print("Secondes elapesed: ", self.end_time - self.start_time)
            exit(1)

        self.logger.warning("sent {} images".format(self.sent))

        self.sent += 1
        if self.sent % 20 == 9:
            raise ValueError("BOOOOM!")

        time.sleep(.5)

        return ImgMessage(current_time=time.time(), image=self.img)


class StreamImgService2(StreamImgService):

    def execute(self, inputs):
        msg = super(StreamImgService2, self).execute(inputs)

        msg.image = msg.image // 2

        return msg


if __name__ == "__main__":
    SICComponentManager([StreamImgService], "local")
