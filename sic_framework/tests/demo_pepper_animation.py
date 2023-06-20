import time

from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest, NaoqiAutonomous
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotion, NaoPostureRequest, NaoqiAnimationRequest

motion = NaoqiMotion(ip="192.168.0.148")

a = NaoPostureRequest("Stand", .5)

reply = motion.request(a)


print("Saying yes!")
motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_3"))




autonomous = NaoqiAutonomous(ip="192.168.0.148")

a = NaoRestRequest()
autonomous.request(a)
