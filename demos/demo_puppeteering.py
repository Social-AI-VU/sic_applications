import time
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoBasicAwarenessRequest, NaoBackgroundMovingRequest, NaoRestRequest
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import StartStreaming, StopStreaming, NaoMotionStreamerConf
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

JOINTS = ["Head", "RArm", "LArm"]
FIXED_JOINTS = ["RLeg", "LLeg"]


conf = NaoMotionStreamerConf(samples_per_second=30)
puppet_master = Nao("192.168.0.191", motion_stream_conf=conf)
puppet_master.autonomous.request(NaoBasicAwarenessRequest(False))
puppet_master.autonomous.request(NaoBackgroundMovingRequest(False))
puppet_master.stiffness.request(Stiffness(0.0, joints=JOINTS))

puppet = Nao("192.168.0.239")
puppet.autonomous.request(NaoBasicAwarenessRequest(False))
puppet.autonomous.request(NaoBackgroundMovingRequest(False))
puppet.stiffness.request(Stiffness(0.5, joints=JOINTS))

# Set fixed joints to high stiffness such that the robots don't fall
puppet_master.stiffness.request(Stiffness(0.7, joints=FIXED_JOINTS))
puppet.stiffness.request(Stiffness(0.7, joints=FIXED_JOINTS))

# Start both robots in rest pose
puppet.autonomous.request(NaoRestRequest())
puppet_master.autonomous.request(NaoRestRequest())

# Connect the puppet master with the puppet
puppet.motion_streaming.connect(puppet_master.motion_streaming)

# Start the puppeteering and let Nao say that you can start
puppet_master.motion_streaming.request(StartStreaming(JOINTS))
puppet_master.tts.request(NaoqiTextToSpeechRequest("Start puppeteering", language="English", animated=True))

# Wait 30 seconds for puppeteering
time.sleep(30)

# Done puppeteering, let Nao say it's finished, and reset stiffness
puppet_master.tts.request(NaoqiTextToSpeechRequest("We are done puppeteering", language="English", animated=True))
puppet_master.stiffness.request(Stiffness(0.7, joints=JOINTS))
puppet_master.motion_streaming.request(StopStreaming())

# Set both robots in rest pose again
puppet.autonomous.request(NaoRestRequest())
puppet_master.autonomous.request(NaoRestRequest())

print("DONE")
