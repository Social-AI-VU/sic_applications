"""
This demo shows how to make Nao perform predefined postures and animations.
"""
import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
)
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
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
    logger.info("Starting Nao Motion Demo...")
    # nao = Nao(ip="XXX")
    # nao = Nao(ip="10.0.0.241", dev_test=True, test_repo="/Users/apple/Desktop/SAIL/SIC_Development/social-interaction-cloud")
    nao = Nao(ip="10.0.0.241", dev_test=True)

    # For a list of postures, see NaoPostureRequest class or
    # http://doc.aldebaran.com/2-4/family/robots/postures_robot.html#robot-postures
    logger.info("Requesting Stand posture")
    nao.motion.request(NaoPostureRequest("Stand", 0.5))
    time.sleep(1)

    #}A list of all Nao animations can be found here: http://doc.aldebaran.com/2-4/naoqi/motion/alanimationplayer-advanced.html#animationplayer-list-behaviors-nao
    logger.info("Playing Hey gesture animation")
    nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"))
    time.sleep(1)
    
    logger.info("Motion demo completed successfully")
except Exception as e:
    logger.error("Error in motion demo: {e}".format(e=e))
finally:
    logger.info("Shutting down application")
    app.shutdown()
