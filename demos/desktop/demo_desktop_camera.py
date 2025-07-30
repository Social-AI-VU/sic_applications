""" 
This demo displays a camera image from your webcam on your laptop.

NOTE:
If you want to use cv2 to display an image in a window, you need to call cv2.imshow() in the main thread.
It is not possible to call cv2.imshow() in a background process (such as the message handler of a Component).
This is why we need to register a callback function to receive the image and display it in the main thread.
"""

from my_sic import sic_app

from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
import queue
import cv2

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
