import time

import cv2

from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.desktop.desktop_camera import DesktopCamera

""" 
This demo should display a camera image from your webcam on your laptop.
"""

def on_image(image_message: CompressedImageMessage):
  image = image_message.image

  cv2.imshow('', image)
  cv2.waitKey(1)

camera = DesktopCamera()

camera.register_callback(on_image)


time.sleep(100)
