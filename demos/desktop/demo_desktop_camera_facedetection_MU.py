import queue
import cv2
from sic_framework.core import utils_cv2
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.face_detection.face_detection import FaceDetection
# CUSTOM FACE DETECTION EXAMPLE
# from custom_components.custom_face_detection import CustomFaceDetection

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.

IMPORTANT
face-detection service needs to be running:
1. run-face-detection
"""

imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)


def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)


def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)


# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)

print("Creating pipeline")

# Connect to the services
desktop = Desktop(camera_conf=conf)

print("Starting desktop camera")

desktop_cam_output = desktop.camera.output_channel

print("Setting up face detection service")

face_rec = FaceDetection()

print("Connecting face detection service to camera")

# Feed the camera images into the face recognition component
face_rec_output = face_rec.connect(input_channel=desktop_cam_output)

print("Subscribing callback functions")

# Send back the outputs to this program
desktop.camera.register_callback(output_channel=desktop_cam_output, callback=on_image)
face_rec.register_callback(output_channel=face_rec_output, callback=on_faces)

print("Starting main loop")

while True:
    img = imgs_buffer.get()
    faces = faces_buffer.get()

    for face in faces:
        utils_cv2.draw_bbox_on_image(face, img)

    cv2.imshow("", img)
    cv2.waitKey(1)
