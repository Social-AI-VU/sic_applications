import time

import cv2

from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCamera


def on_image(image_message: CompressedImageMessage):
  cv2.imshow('', image_message.image[:,:,::-1])
  cv2.waitKey(1)


camera = TopNaoCamera(ip="192.168.0.210")
camera.register_callback(on_image)


time.sleep(100)
