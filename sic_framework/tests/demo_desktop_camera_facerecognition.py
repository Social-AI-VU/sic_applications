import queue

import cv2

from sic_framework.core.message_python2 import BoundingBoxesMessage
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.core.utils_cv2 import draw_bbox_on_image
from sic_framework.devices.desktop.desktop_camera import DesktopCamera
from sic_framework.services.face_recognition_dnn.face_recognition import DNNFaceRecognition

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.
"""

imgs_buffer = queue.Queue()


def on_image(image_message: CompressedImageMessage):
    try:
        imgs_buffer.get_nowait()  # remove previous message if its still there
    except queue.Empty:
        pass
    imgs_buffer.put(image_message.image)


faces_buffer = queue.Queue()


def on_faces(message: BoundingBoxesMessage):
    try:
        faces_buffer.get_nowait()  # remove previous message if its still there
    except queue.Empty:
        pass
    faces_buffer.put(message.bboxes)


# Connect to the services
camera = DesktopCamera()
face_rec = DNNFaceRecognition()

# Feed the camera images into the face recognition component
face_rec.connect(camera)

# Send back the outputs to this program
camera.register_callback(on_image)
face_rec.register_callback(on_faces)

while True:
    img = imgs_buffer.get()
    faces = faces_buffer.get()

    for face in faces:
        draw_bbox_on_image(face, img)

    cv2.imshow('', img)
    cv2.waitKey(1)
