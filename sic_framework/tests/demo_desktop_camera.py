import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.desktop.desktop_camera import DesktopCamera
import queue

""" 
This demo should display a camera image from your webcam on your laptop.
"""

imgs = queue.Queue()
def on_image(image_message: CompressedImageMessage):
  imgs.put(image_message.image)


camera = DesktopCamera()
camera.register_callback(on_image)

while True:
  img = imgs.get()
  cv2.imshow('', img)
  cv2.waitKey(1)
