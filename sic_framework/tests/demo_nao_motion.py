import time

from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotion, NaoPostureRequest, NaoRestRequest

motion = NaoqiMotion(ip="192.168.0.151")

a = NaoPostureRequest("Stand", .5)

reply = motion.request(a)

time.sleep(1)

a = NaoPostureRequest("Crouch", .5)

reply = motion.request(a)

a = NaoRestRequest()

motion.request(a)
