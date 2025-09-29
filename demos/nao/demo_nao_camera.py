"""
This script demonstrates how to use the Nao camera.
"""

import queue

import cv2
from sic_framework.core.message_python2 import CompressedImageMessage
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiCameraConf
from sic_framework.core.sic_application import (
    set_log_level,
    set_log_file,
    get_app_logger, 
    get_shutdown_event
)
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to logger.info statements.
logger = get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
set_log_level(sic_logging.DEBUG)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = get_shutdown_event()

imgs = queue.Queue()


def on_image(image_message: CompressedImageMessage):
    # we could use cv2.imshow here, but that does not work on Mac OSX
    imgs.put(image_message.image)


# Create camera configuration using vflip to flip the image vertically
# See "NaoqiCameraConf" for more options like brightness, contrast, sharpness, etc
conf = NaoqiCameraConf(vflip=1)

logger.info("Initializing Nao...")
nao = Nao(ip="XX.XX.XX.XX", top_camera_conf=conf)

logger.info("Registering callback...")
nao.top_camera.register_callback(on_image)

logger.info("Starting demo...")
while not shutdown_flag.is_set():
    img = imgs.get()
    cv2.imshow("", img[..., ::-1])  # cv2 is BGR instead of RGB
    cv2.waitKey(1)
