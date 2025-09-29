"""
This demo shows how to make Nao perform predefined postures and animations.
"""
import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
)
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

nao = Nao(ip="XXX")

# For a list of postures, see NaoPostureRequest class or
# http://doc.aldebaran.com/2-4/family/robots/postures_robot.html#robot-postures
nao.motion.request(NaoPostureRequest("Stand", 0.5))
time.sleep(1)

# A list of all Nao animations can be found here: http://doc.aldebaran.com/2-4/naoqi/motion/alanimationplayer-advanced.html#animationplayer-list-behaviors-nao
nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"))
time.sleep(1)
