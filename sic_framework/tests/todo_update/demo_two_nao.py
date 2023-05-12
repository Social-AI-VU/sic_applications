import time

import cv2
from sic_framework import SICApplication
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.nao import Nao
from sic_framework.tests.demo_two_nao_service import MergeImages
import tqdm

""" 
This demo should let the robot say "peekaboo" every time its camera is completely dark
"""


class TwoNaos(SICApplication):

    def run(self) -> None:
        naoleft = Nao(device_id='naoleft', application=self)
        naoright = Nao(device_id='naoright', application=self)

        both = self.start_service(MergeImages, device_id='xps15',
                                  inputs_to_service=[naoleft.top_camera, naoright.top_camera])

        for i in tqdm.trange(1000):
            image_message = both.get_output(timeout_approx=20)
            self.on_image(image_message)

    def on_image(self, image_message: CompressedImageMessage):
        cv2.imshow('', image_message.image[..., ::-1])
        cv2.waitKey(1)


if __name__ == '__main__':
    test_app = TwoNaos()

    print("FLUSHING REDIS")
    test_app.redis.flushall()

    test_app.run()

"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/v3/libtubojpeg_robot/lib32/
export DB_IP=192.168.0.FOO
"""
