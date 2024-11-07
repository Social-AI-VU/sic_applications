import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import (
    NaoqiMotionRecorderConf,
    NaoqiMotionRecording,
    PlayRecording,
    StartRecording,
    StopRecording,
)
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness

"""
This demo shows how to record and replay a motion on a Nao robot.
"""

conf = NaoqiMotionRecorderConf(use_sensors=True)
nao = Nao("192.168.2.7", motion_record_conf=conf)

chain = ["LArm", "RArm"]
record_time = 10
MOTION_NAME = "my_motion"

# Disable stiffness such that we can move it by hand
nao.stiffness.request(Stiffness(stiffness=0.0, joints=chain))

# Start recording
print("Start moving the robot! (not too fast)")
nao.motion_record.request(StartRecording(chain))
time.sleep(record_time)

# Save the recording
print("Saving action")
recording = nao.motion_record.request(StopRecording())
recording.save(MOTION_NAME)

# Replay the recording
print("Replaying action")
nao.stiffness.request(
    Stiffness(stiffness=0.7, joints=chain)
)  # Enable stiffness for replay
recording = NaoqiMotionRecording.load(MOTION_NAME)
nao.motion_record.request(PlayRecording(recording))
