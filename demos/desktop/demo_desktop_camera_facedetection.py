from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.services.face_detection.face_detection import FaceDetection
from sic_framework.devices.desktop import Desktop
from sic_framework.core.message_python2 import (
    BoundingBoxesMessage,
    CompressedImageMessage,
)
from sic_framework.core import utils
from sic_framework.core import utils_cv2
import queue
import cv2

# CUSTOM FACE DETECTION EXAMPLE
# from custom_components.custom_face_detection import CustomFaceDetection

""" 
This demo recognizes faces from your webcam and displays the result on your laptop.

IMPORTANT
face-detection service needs to be running:
1. run-face-detection
"""

print(f"IP address of current machine: {utils.get_ip_adress()}")

imgs_buffer = queue.Queue(maxsize=1)
faces_buffer = queue.Queue(maxsize=1)


def on_image(image_message: CompressedImageMessage):
    imgs_buffer.put(image_message.image)


def on_faces(message: BoundingBoxesMessage):
    faces_buffer.put(message.bboxes)


# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)

print("Creating pipeline...")

# Connect to the services
desktop = Desktop(camera_conf=conf)

print("Starting desktop camera")

desktop_cam = desktop.camera

print("Setting up face detection service")

face_dec = FaceDetection(input_source=desktop_cam)

print("Subscribing callback functions")

# Send back the outputs to this program
desktop_cam.register_callback(callback=on_image)
face_dec.register_callback(callback=on_faces)

print("Starting main loop")

while True:
    img = imgs_buffer.get()
    faces = faces_buffer.get()

    for face in faces:
        utils_cv2.draw_bbox_on_image(face, img)

    cv2.imshow("", img)
    cv2.waitKey(1)
