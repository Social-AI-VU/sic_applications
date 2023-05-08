import time

import cv2

import tqdm

from sic_framework.core import utils_cv2
from sic_framework.devices.nao import Nao

from sic_framework import SICApplication, BoundingBoxesMessage
from sic_framework.devices.common_naoqi.naoqi_camera import TopNaoCameraSensor, CompressedImageMessage
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
    utils_cv2.draw_on_image(face, image)

  cv2.imshow('', image)
  cv2.waitKey(1)


nao = Nao(ip="192.168.0.1")

nao.top_camera.register_callback(on_image)


face_recognition = DNNFaceRecognition(ip='localhost')

face_recognition.connect(nao.top_camera)

face_recognition.register_callback(on_detected_faces)



time.sleep(100)
