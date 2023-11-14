import queue

import cv2

from sic_framework.core.message_python2 import BoundingBoxesMessage
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.core.utils_cv2 import draw_bbox_on_image
from sic_framework.devices.desktop import Desktop
from sic_framework.services.face_detection_dnn.face_detection_dnn import DNNFaceDetection

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.

You should have started the face detection service first with:
[services/face_detection_dnn/] python face_detection_dnn.py
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
desktop = Desktop()
face_rec = DNNFaceDetection()

# Feed the camera images into the face recognition component
face_rec.connect(desktop.camera)

# Send back the outputs to this program
desktop.camera.register_callback(on_image)
face_rec.register_callback(on_faces)

while True:
    img = imgs_buffer.get()
    faces = faces_buffer.get()

    for face in faces:
        draw_bbox_on_image(face, img)

    cv2.imshow('', img)
    cv2.waitKey(1)
