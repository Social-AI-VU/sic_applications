import queue
import cv2

from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoqiCamera


imgs = queue.Queue()
def on_image(image_message: CompressedImageMessage):
    # we could cv2.imshow here, but that does not work on Mac OSX
    imgs.put(image_message.image)


camera = TopNaoqiCamera(ip="192.168.0.210")
camera.register_callback(on_image)

while True:
    img = imgs.get()
    cv2.imshow('', img)
    cv2.waitKey(1)
