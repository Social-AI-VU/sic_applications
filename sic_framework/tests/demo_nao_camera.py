import queue
import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices import Nao, Pepper
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCamera

imgs = queue.Queue()
def on_image(image_message: CompressedImageMessage):
    # we could cv2.imshow here, but that does not work on Mac OSX
    imgs.put(image_message.image)


# nao = Nao(ip="10.15.3.90")
nao = Pepper(ip="192.168.0.165")
# top_camera = NaoqiTopCamera(ip="10.15.3.226")
nao.top_camera.register_callback(on_image)

for i in range(100):
    img = imgs.get()
    cv2.imshow('', img)
    cv2.waitKey(1)
