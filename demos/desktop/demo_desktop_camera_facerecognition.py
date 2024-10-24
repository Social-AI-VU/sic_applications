import queue

import cv2
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.core.utils_cv2 import draw_bbox_on_image
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.face_recognition_dnn.face_recognition import (
    DNNFaceRecognition,
)

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.

IMPORTANT
face-detection service needs to be running:
1. pip install social-interaction-cloud[face-recognition]
2. run-face-recognition --model xxx.pt --cascadefile xxx.xml

"""

imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)


def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)


def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)


# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(
    fx=0.3, fy=0.3, flip=1
)  # You might want to set fx and fy to 0.3 on a slower machine

# Connect to the services
desktop = Desktop(camera_conf=conf)
face_rec = DNNFaceRecognition()

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

    cv2.imshow("", img)
    cv2.waitKey(1)
