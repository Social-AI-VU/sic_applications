import time

import numpy as np

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionTools
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoqiMotionRecorder, StartRecording, StopRecording, \
    PlayRecording, NaoqiMotionRecorderConf
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness

conf = NaoqiMotionRecorderConf(use_sensors=True)
nao = Nao("10.0.0.236", motion_record_conf=conf)

# Disable stiffness such that we can move it by hand
nao.stiffness.request(Stiffness(stiffness=0.0, joints=["LArm"]))

nao.motion_record.request(StartRecording(["LArm"]))



print("Start moving the robot! (not too fast)")

record_time = 10

time.sleep(record_time)

recording = nao.motion_record.request(StopRecording())
print("Done")

print(recording)


print("Replaying action at twice the speed")

# Enable stiffness such the robot can move itself
nao.stiffness.request(Stiffness(stiffness=0.7, joints=["LArm"]))


nao.motion_record.request(PlayRecording(recording, playback_speed=2))

time.sleep(record_time)
print("end")
