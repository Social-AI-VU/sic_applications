""" 
This demo recognizes faces from your webcam and displays the result on your laptop.

NOTE:
If you want to display the image in a window, you need to call cv2.imshow() in the main thread.
It is not possible to call cv2.imshow() in a background process (such as the message handler of a Component).
This is why we need to register a callback function to receive the image and display it in the main thread.

IMPORTANT
face-detection service needs to be running:
1. run-face-detection
"""

from my_sic import sic_app

from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.services.face_detection.face_detection import FaceDetection, FaceDetectionConf
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

imgs = queue.Queue()

def on_image(image_message: CompressedImageMessage):
    imgs.put(image_message.image)


print(f"IP address of current machine: {utils.get_ip_adress()}")

print("Creating pipeline...")

# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
camera_conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=1)

# Connect to the services
desktop = Desktop(camera_conf=camera_conf)

print("Starting desktop camera")

desktop_cam = desktop.camera

print("Starting face detection service")

face_dec_conf = FaceDetectionConf(merge_image=True)
face_dec = FaceDetection(input_source=desktop_cam, conf=face_dec_conf)

print("Subscribing callback function")
face_dec.register_callback(callback=on_image)

print("Starting main loop...")
while True:
    img = imgs.get()
    cv2.imshow("", img)
    cv2.waitKey(1)