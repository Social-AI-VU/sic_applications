import time

import cv2

import cv2
import numpy as np
from sic_framework import SICApplication
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechActuator, NaoqiTextToSpeechRequest
from sic_framework.devices.nao import Nao

""" 
This demo should let the robot say "peekaboo" every time its camera is completely dark
"""


class DemoPeekABoo(SICApplication):

    def run(self) -> None:
        self.nao = Nao(device_id='nao', application=self)

        self.nao.top_camera.register_callback(self.on_image)

        time.sleep(20)

    def on_image(self, image_message: CompressedImageMessage):
        cv2.imshow('', image_message.image[..., ::-1])
        cv2.waitKey(1)

        image = image_message.image

        print("peekaboo?", np.median(image))
        if np.median(image) < 2:
            self.nao.tts.send_message(NaoqiTextToSpeechRequest('peekaboo!'))


if __name__ == '__main__':
    test_app = DemoPeekABoo()

    test_app.run()

    test_app.stop()
"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/v3/libtubojpeg_robot/lib32/
export DB_IP=192.168.0.FOO
"""
