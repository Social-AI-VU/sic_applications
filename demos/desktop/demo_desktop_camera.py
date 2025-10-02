""" 
This demo displays a camera image from your webcam on your laptop.
"""

import queue

import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices.common_desktop.desktop_camera import DesktopCameraConf
from sic_framework.devices.desktop import Desktop
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to print statements.
app = SICApplication()
logger = app.get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
app.set_log_level(sic_logging.INFO)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# app.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = app.get_shutdown_event()

imgs = queue.Queue()

def on_image(image_message: CompressedImageMessage):
    imgs.put(image_message.image)

# Create camera configuration using fx and fy to resize the image along x- and y-axis, and possibly flip image
conf = DesktopCameraConf(fx=1.0, fy=1.0, flip=-1)
desktop = Desktop(camera_conf=conf)

desktop_cam = desktop.camera

logger.info("Subscribing callback function")
desktop_cam.register_callback(callback=on_image)

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
    logger.info("Cleaning up...")
    cv2.destroyAllWindows()
except Exception as e:
    logger.error("Exception: {}".format(e))
finally:
    app.shutdown()