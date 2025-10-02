"""
This script demonstrates how to use the Nao LEDs.
"""

import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_leds import (
    NaoFadeRGBRequest,
    NaoLEDRequest,
)
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

app = SICApplication()
# In case you want to use the logger with a neat format as opposed to logger.info statements.
logger = app.get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
app.set_log_level(sic_logging.DEBUG)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# app.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = app.get_shutdown_event()

try:
    logger.info("Starting Nao LEDs Demo...")
    nao = Nao(ip="10.0.0.241", dev_test=True, test_repo="/Users/apple/Desktop/SAIL/SIC_Development/social-interaction-cloud")

    logger.info("Requesting Eye LEDs to turn on")
    reply = nao.leds.request(NaoLEDRequest("FaceLeds", True))
    time.sleep(1)

    logger.info("Setting right Еye LEDs to red")
    reply = nao.leds.request(NaoFadeRGBRequest("RightFaceLeds", 1, 0, 0, 0))

    time.sleep(1)

    logger.info("Setting left Eye LEDs to blue")
    reply = nao.leds.request(NaoFadeRGBRequest("LeftFaceLeds", 0, 0, 1, 0))

    logger.info("LEDs demo completed successfully")
except Exception as e:
    logger.error("Error in LEDs demo: {e}".format(e=e))
finally:
    app.shutdown()