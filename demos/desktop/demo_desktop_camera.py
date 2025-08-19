""" 
This demo displays a camera image from your webcam on your laptop.
"""

import queue

import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.core import sic_application

imgs = queue.Queue()

def on_image(image_message: CompressedImageMessage):
    imgs.put(image_message.image)

# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=-1)
desktop = Desktop(camera_conf=conf)

desktop_cam = desktop.camera

print("Subscribing callback function")
desktop_cam.register_callback(callback=on_image)

print("Starting main loop")
while True:
    img = imgs.get()
    cv2.imshow("", img)
    cv2.waitKey(1)
