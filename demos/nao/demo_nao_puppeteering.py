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

JOINTS = ["Head", "RArm", "LArm"]
FIXED_JOINTS = ["RLeg", "LLeg"]


conf = NaoMotionStreamerConf(samples_per_second=30)
puppet_master = Nao("XXX", motion_stream_conf=conf)
puppet_master.autonomous.request(NaoBasicAwarenessRequest(False))
puppet_master.autonomous.request(NaoBackgroundMovingRequest(False))
puppet_master.stiffness.request(Stiffness(stiffness=0.0, joints=JOINTS))
puppet_master_motion = puppet_master.motion_streaming()

puppet = Nao("XXX")
puppet.autonomous.request(NaoBasicAwarenessRequest(False))
puppet.autonomous.request(NaoBackgroundMovingRequest(False))
puppet.stiffness.request(Stiffness(0.5, joints=JOINTS))
puppet_motion = puppet.motion_streaming(input_source=puppet_master_motion)

# Set fixed joints to high stiffness such that the robots don't fall
puppet_master.stiffness.request(Stiffness(0.7, joints=FIXED_JOINTS))
puppet.stiffness.request(Stiffness(0.7, joints=FIXED_JOINTS))

# Start both robots in rest pose
puppet.autonomous.request(NaoRestRequest())
puppet_master.autonomous.request(NaoRestRequest())

# Start the puppeteering and let Nao say that you can start
puppet_master_motion.request(StartStreaming(JOINTS))
puppet_master.tts.request(
    NaoqiTextToSpeechRequest("Start puppeteering", language="English", animated=True)
)

# Wait 30 seconds for puppeteering
time.sleep(30)

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

print("DONE")
