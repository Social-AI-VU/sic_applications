"""
This demo shows you how to make Nao
1. Track a face with its head.
2. Move its end-effector (both arms in this case) to track a red ball, given a position relative to the ball.
"""

import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_tracker import (
    RemoveTargetRequest,
    StartTrackRequest,
    StopAllTrackRequest,
)
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
app = SICApplication()
logger = app.get_app_logger()
app.set_log_level(sic_logging.DEBUG)

try:
    # Connect to NAO
    nao = Nao(ip="XXX")

    # Start tracking a face
    target_name = "Face"

    # Enable stiffness so the head joint can be actuated
    nao.stiffness.request(Stiffness(stiffness=1.0, joints=["Head"]))
    nao.tracker.request(
        StartTrackRequest(target_name=target_name, size=0.2, mode="Head", effector="None")
    )

    # Wait for a specific time
    time.sleep(10)

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

    # Wait for a specific time
    time.sleep(10)

    # Stop tracking everything
    nao.tracker.request(StopAllTrackRequest())
except Exception as e:
    logger.error("Error in tracker demo: {e}".format(e=e))
finally:
    app.shutdown()