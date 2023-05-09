import time
from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import BoundingBoxesMessage, CompressedImageMessage
from sic_framework.devices.desktop.desktop_camera import DesktopCamera
from sic_framework.services.face_detection.face_detection_service import FaceDetection

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


# nao = Nao(ip="192.168.0.1")
# camera = nao.top_camera


camera = DesktopCamera()
camera.register_callback(on_image)

face_recognition = FaceDetection(ip='localhost')
face_recognition.connect(camera)
face_recognition.register_callback(on_detected_faces)

time.sleep(100)
