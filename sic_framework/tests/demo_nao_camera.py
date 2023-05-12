import time

import cv2

from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import BoundingBoxesMessage, CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCamera
from sic_framework.devices.desktop.desktop_camera import DesktopCamera
from sic_framework.services.face_detection.face_detection_service import FaceDetection
from sic_framework.services.face_recognition_dnn.face_recognition_service import DNNFaceRecognition





def on_image(image_message: CompressedImageMessage):
  cv2.imshow('', image_message.image[:,:,::-1])
  cv2.waitKey(1)


camera = TopNaoCamera(ip="192.168.0.151")
camera.register_callback(on_image)


time.sleep(100)
