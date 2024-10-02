import time

from sic_framework.devices import Pepper, Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoRestRequest, NaoqiAutonomous
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotion, NaoPostureRequest, NaoqiAnimationRequest


robot = Pepper(ip="10.15.3.226")


a = NaoPostureRequest("Stand", .5)

reply = robot.motion.request(a)


print("Saying yes!")
robot.motion.request(NaoqiAnimationRequest("animations/Stand/Gestures/Hey_3"))




# set the robot to rest mode.
a = NaoRestRequest()
robot.autonomous.request(a)
