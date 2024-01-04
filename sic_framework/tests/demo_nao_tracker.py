import time
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_tracker import StartTrackRequest, StopAllTrackRequest, RemoveTargetRequest
from sic_framework.devices.common_naoqi.naoqi_motion import NaoPostureRequest

"""
This demo shows you how to make Nao track a face, walk to you given a position relative to the face,
and later move an end-effector (both arms in this case) to track a red ball
"""

# Connect to NAO
nao = Nao(ip="192.168.0.165")

# start tracking a face
target_name = "Face"
# set the robot relative position to target
# the robot stays a 30 centimeters of target with 10 cm precision
move_rel_position = [-0.3, 0.0, 0.0, 0.1, 0.1, 0.1]
nao.tracker.request(StartTrackRequest(target_name, 0.2, "Move", effector="None", move_rel_position=move_rel_position))

# Do some stuff here
time.sleep(20)

# unregister target face
nao.tracker.request(RemoveTargetRequest(target_name))

# start tracking a red ball
target_name = "RedBall"
nao.tracker.request(StartTrackRequest(target_name, 0.06, "Head", effector="Arms"))

# Do some stuff here
time.sleep(20)

# Stop tracking everything
nao.tracker.request(StopAllTrackRequest())
