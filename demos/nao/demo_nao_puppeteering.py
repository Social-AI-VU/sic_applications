import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBackgroundMovingRequest,
    NaoBasicAwarenessRequest,
    NaoRestRequest,
)
from sic_framework.devices.common_naoqi.nao_motion_streamer import (
    NaoMotionStreamerConf,
    StartStreaming,
    StopStreaming,
)
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Create the SICApplication instance to be able to use the logger and the shutdown event
app = SICApplication()
logger = app.get_app_logger()
app.set_log_level(sic_logging.DEBUG)

logger.info("Starting Nao Puppeteering Demo...")

try:
    JOINTS = ["Head", "RArm", "LArm"]
    FIXED_JOINTS = ["RLeg", "LLeg"]

    logger.info("Initializing puppet master...")

    conf = NaoMotionStreamerConf(samples_per_second=30)
    puppet_master = Nao("10.0.0.241", dev_test=True, motion_stream_conf=conf)
    puppet_master.autonomous.request(NaoBasicAwarenessRequest(False))
    puppet_master.autonomous.request(NaoBackgroundMovingRequest(False))
    puppet_master.stiffness.request(Stiffness(stiffness=0.0, joints=JOINTS))
    puppet_master_motion = puppet_master.motion_streaming()

    logger.info("Initializing puppet...")
    puppet = Nao("10.0.0.236", dev_test=True)
    puppet.autonomous.request(NaoBasicAwarenessRequest(False))
    puppet.autonomous.request(NaoBackgroundMovingRequest(False))
    puppet.stiffness.request(Stiffness(0.5, joints=JOINTS))
    puppet_motion = puppet.motion_streaming(input_source=puppet_master_motion)

    logger.info("Setting fixed joints to high stiffness...")
    # Set fixed joints to high stiffness such that the robots don't fall
    puppet_master.stiffness.request(Stiffness(0.7, joints=FIXED_JOINTS))
    puppet.stiffness.request(Stiffness(0.7, joints=FIXED_JOINTS))

    logger.info("Starting both robots in rest pose...")
    # Start both robots in rest pose
    puppet.autonomous.request(NaoRestRequest())
    puppet_master.autonomous.request(NaoRestRequest())

    logger.info("Starting puppeteering...")
    # Start the puppeteering and let Nao say that you can start
    puppet_master_motion.request(StartStreaming(JOINTS))
    puppet_master.tts.request(
        NaoqiTextToSpeechRequest("Start puppeteering", language="English", animated=True)
    )

    # Wait 30 seconds for puppeteering
    time.sleep(30)

    logger.info("Done puppeteering...")
    # Done puppeteering, let Nao say it's finished, and reset stiffness
    puppet_master.tts.request(
        NaoqiTextToSpeechRequest(
            "We are done puppeteering", language="English", animated=True
        )
    )
    puppet_master.stiffness.request(Stiffness(0.7, joints=JOINTS))
    puppet_master_motion.request(StopStreaming())

    # Set both robots in rest pose again
    puppet.autonomous.request(NaoRestRequest())
    puppet_master.autonomous.request(NaoRestRequest())

    logger.info("Puppeteering demo completed successfully")
except Exception as e:
    logger.error("Error in puppeteering demo: {e}".format(e=e))
finally:
    app.shutdown()