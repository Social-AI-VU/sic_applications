import time

import cv2

from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import BoundingBoxesMessage, CompressedImageMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCamera
from sic_framework.devices.desktop.desktop_camera import DesktopCamera
from sic_framework.services.face_detection.face_detection_service import FaceDetection
from sic_framework.services.face_recognition_dnn.face_recognition_service import DNNFaceRecognition


""" 
This demo should display a camera image from a NAO robot on your laptop.
"""

faces = []
def on_detected_faces(boundingboxes: BoundingBoxesMessage):
  global faces
  faces = boundingboxes.bboxes


def on_image(image_message: CompressedImageMessage):
  image = image_message.image

  for face in faces:
    print(face.identifier)
    utils_cv2.draw_on_image(face, image)

  cv2.imshow('', image[:,:,::-1])
  cv2.waitKey(1)


# camera = DesktopCamera()
camera = TopNaoCamera(ip="192.168.0.236")
camera.register_callback(on_image)

face_recognition = DNNFaceRecognition(ip='localhost')
face_recognition.connect(camera)
face_recognition.register_callback(on_detected_faces)

time.sleep(100)
