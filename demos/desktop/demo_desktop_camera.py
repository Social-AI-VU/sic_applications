""" 
This demo displays a camera image from your webcam on your laptop.
"""

import queue

import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.core import sic_application
from sic_framework.core.sic_application import get_app_logger

logger = get_app_logger()

imgs = queue.Queue()

def on_image(image_message: CompressedImageMessage):
    imgs.put(image_message.image)

# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=-1)
desktop = Desktop(camera_conf=conf)

desktop_cam = desktop.camera

logger.info("Subscribing callback function")
desktop_cam.register_callback(callback=on_image)

# Get the shared shutdown event from sic_application
shutdown_flag = sic_application.get_shutdown_event()

logger.info("Starting main loop")
try:
    while not shutdown_flag.is_set():
        try:
            # Use timeout to make the queue operation non-blocking
            img = imgs.get(timeout=0.1)  # 100ms timeout
            cv2.imshow("Camera Feed", img)
            cv2.waitKey(1)
        except queue.Empty:
            # No new image, continue loop to check shutdown flag
            continue
except KeyboardInterrupt:
    logger.info("Keyboard interrupt received")
finally:
    logger.info("Cleaning up...")
    cv2.destroyAllWindows()