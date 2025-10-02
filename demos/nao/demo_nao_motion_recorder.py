"""
This demo shows how to record and replay a motion on a Nao robot.
"""
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
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
app = SICApplication()
logger = app.get_app_logger()
app.set_log_level(sic_logging.DEBUG)

try:
    conf = NaoqiMotionRecorderConf(use_sensors=True)
    # nao = Nao("10.0.0.241", dev_test=True, test_repo="/Users/apple/Desktop/SAIL/SIC_Development/social-interaction-cloud", motion_record_conf=conf)
    nao = Nao("10.0.0.241", dev_test=True, motion_record_conf=conf)
    # nao = Nao("XXX", motion_record_conf=conf)

    chain = ["LArm", "RArm"]
    record_time = 10
    MOTION_NAME = "my_motion"

    # Disable stiffness such that we can move it by hand
    nao.stiffness.request(Stiffness(stiffness=0.0, joints=chain))

    # Start recording
    logger.info("Start moving the robot! (not too fast)")
    nao.motion_record.request(StartRecording(chain))
    time.sleep(record_time)

    # Save the recording
    logger.info("Saving action")
    recording = nao.motion_record.request(StopRecording())
    recording.save(MOTION_NAME)

    # Replay the recording
    logger.info("Replaying action")
    nao.stiffness.request(
        Stiffness(stiffness=0.7, joints=chain)
    )  # Enable stiffness for replay
    recording = NaoqiMotionRecording.load(MOTION_NAME)
    nao.motion_record.request(PlayRecording(recording))
except Exception as e:
    logger.error(f"Exception: {e}")
finally:
    app.shutdown()
