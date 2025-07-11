import queue

import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiCameraConf

imgs = queue.Queue()


def on_image(image_message: CompressedImageMessage):
    # we could use cv2.imshow here, but that does not work on Mac OSX
    imgs.put(image_message.image)


# Create camera configuration using vflip to flip the image vertically
# See "NaoqiCameraConf" for more options like brightness, contrast, sharpness, etc
conf = NaoqiCameraConf(vflip=1)

print("Initializing Nao...")
nao = Nao(ip="10.0.0.198", top_camera_conf=conf, dev_test=True, test_repo="/Users/apple/Desktop/SAIL/SIC_Development/social-interaction-cloud")

print("Registering callback...")
nao.top_camera.register_callback(on_image)

print("Starting demo...")
while True:
    img = imgs.get()
    cv2.imshow("", img[..., ::-1])  # cv2 is BGR instead of RGB
    cv2.waitKey(1)
