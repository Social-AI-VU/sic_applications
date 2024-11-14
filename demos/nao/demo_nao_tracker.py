import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_tracker import (
    RemoveTargetRequest,
    StartTrackRequest,
    StopAllTrackRequest,
)

"""
This demo shows you how to make Nao
1. Track a face with its head.
2. Move its end-effector (both arms in this case) to track a red ball, given a position relative to the ball.
"""

# Connect to NAO
nao = Nao(ip="10.0.0.242")

# Start tracking a face
target_name = "Face"

# Enable stiffness so the head joint can be actuated
nao.stiffness.request(Stiffness(stiffness=1.0, joints=["Head"]))
nao.tracker.request(
    StartTrackRequest(target_name=target_name, size=0.2, mode="Head", effector="None")
)

# Do some stuff here
time.sleep(30)

# Unregister target face
nao.tracker.request(RemoveTargetRequest(target_name))

# Start tracking a red ball using nao's arms
# Set a robot position relative to target so that the robot stays a 30 centimeters (along x axis) with 10 cm threshold
target_name = "RedBall"
move_rel_position = [-0.3, 0.0, 0.0, 0.1, 0.1, 0.1]
nao.tracker.request(
    StartTrackRequest(
        target_name=target_name,
        size=0.06,
        mode="Move",
        effector="Arms",
        move_rel_position=move_rel_position,
    )
)

# Do some stuff here
time.sleep(30)

# Stop tracking everything
nao.tracker.request(StopAllTrackRequest())
