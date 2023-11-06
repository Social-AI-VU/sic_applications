import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
import queue

from sic_framework.devices.desktop import Desktop

""" 
This demo should display a camera image from your webcam on your laptop.
"""

imgs = queue.Queue()


def on_image(image_message: CompressedImageMessage):
    imgs.put(image_message.image)


desktop = Desktop()

desktop.camera.register_callback(on_image)

while True:
    img = imgs.get()
    cv2.imshow('', img)
    cv2.waitKey(1)
