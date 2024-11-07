import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
)

"""
This demo shows how to make Nao perform predefined postures and animations.
"""

nao = Nao(ip="192.168.0.0")

# For a list of postures, see NaoPostureRequest class or
# http://doc.aldebaran.com/2-4/family/robots/postures_robot.html#robot-postures
nao.motion.request(NaoPostureRequest("Stand", 0.5))
time.sleep(1)

# A list of all Nao animations can be found here: http://doc.aldebaran.com/2-4/naoqi/motion/alanimationplayer-advanced.html#animationplayer-list-behaviors-nao
nao.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_1"))
time.sleep(1)
