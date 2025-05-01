import time

from sic_framework.devices import Pepper
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoBackgroundMovingRequest,
    NaoBasicAwarenessRequest,
    NaoRestRequest,
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
)
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoPostureRequest,
    NaoqiAnimationRequest,
    NaoqiSmartStiffnessRequest,
)
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import (
    NaoqiTextToSpeechRequest,
)
from sic_framework.devices.common_naoqi.pepper_motion_streamer import (
    PepperMotionStreamerConf,
    StartStreaming,
    StopStreaming,
)

JOINTS = ["Head", "RArm", "LArm"]
# FIXED_JOINTS = ["RLeg", "LLeg"]


class PuppeteerApplication:
    def __init__(self, master_ip="10.0.0.165", puppet_ip="10.0.0.196"):

        self.conf = PepperMotionStreamerConf(samples_per_second=30)
        # set the stiffness of the puppet to 1 to control the joints fully, default is 0.6
        self.puppet_conf = PepperMotionStreamerConf(stiffness=1)

        # self.puppet_master = Pepper(
        #     master_ip,
        #     motion_stream_conf=self.conf,
        #     dev_test=True,
        #     test_repo="/home/karen/social-interaction-cloud",
        # )
        self.puppet_master = Pepper(
            master_ip, pepper_motion_conf=self.conf, dev_test=True
        )
        # self.puppet = Pepper(
        #     puppet_ip,
        #     dev_test=True,
        #     test_repo="/home/karen/social-interaction-cloud",
        # )
        self.puppet = Pepper(
            puppet_ip, pepper_motion_conf=self.puppet_conf, dev_test=True
        )

        self._setup_robots()

        self.is_paused = False

        # register callback for tactile sensor
        self.puppet_master.tactile_sensor.register_callback(self.on_touch)

    def _setup_robots(self):
        print(
            "----------------------------------Turn off the autonomous abilities on the master Pepper----------------------------------"
        )
        # Completely disable all autonomous capabilities (including obstacle avoidance) on the master Pepper to prevent interference
        # all the stiffness of its motors will be off, so it will slouch down
        self.puppet_master.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        # turn off the basic awareness of the puppet, so it doesn't move its head around (but it seems like its still moving)
        # See more details here: http://doc.aldebaran.com/2-5/ref/life/autonomous_abilities_management.html#autonomous-abilities-management
        # to find out if it's possible to enable minimal Autonomous Life without disabling obstacle avoidance functionality
        self.puppet.autonomous.request(NaoBasicAwarenessRequest(False))

        print(
            "----------------------------------Waking up robots----------------------------------"
        )

        # wake up robots (Important: for pepper, the stiffness can't be set when it is in rest mode, unlike nao)
        self.puppet_master.autonomous.request(NaoWakeUpRequest())
        self.puppet.autonomous.request(NaoWakeUpRequest())

        print(
            "----------------------------------Setting stiffness of robots----------------------------------"
        )

        # On Pepper, stiffness somehow can't be set at the individual joint level, so we just pass the chains instead of the joints
        self.puppet_master.stiffness.request(
            Stiffness(0.0, joints=JOINTS, enable_joint_list_generation=False)
        )

    def on_touch(self, message):
        if self.is_paused:
            self.puppet_master.motion_streaming.request(StartStreaming(JOINTS))
            self.is_paused = False
        else:
            self.puppet_master.motion_streaming.request(StopStreaming(JOINTS))
            self.is_paused = True

    def start_puppeteering(self, duration=30):
        print(
            "----------------------------------Starting puppeteering----------------------------------"
        )
        # Input the puppet master's motion streamer into the puppet
        self.puppet.motion_streaming.connect(self.puppet_master.motion_streaming)

        # Start the puppeteering and have Nao say that you can start
        self.puppet_master.motion_streaming.request(StartStreaming(JOINTS))

        self.puppet_master.tts.request(
            NaoqiTextToSpeechRequest("Start puppeteering", language="English")
        )

        # Wait for puppeteering
        time.sleep(duration)

        # Cleanup
        self.puppet_master.tts.request(
            NaoqiTextToSpeechRequest("We are done puppeteering", language="English")
        )

        self.puppet_master.motion_streaming.request(StopStreaming())

        # enable the autonomous life of the master pepper before going to rest
        self.puppet_master.autonomous.request(NaoSetAutonomousLifeRequest("solitary"))

        # Set both robots in rest pose again
        self.puppet_master.autonomous.request(NaoRestRequest())
        self.puppet.autonomous.request(NaoRestRequest())
        # use it when you don't want to make peppers rest after every experiment
        # self.puppet.stiffness.request(Stiffness(0, joints=JOINTS, enable_joint_list_generation=False))


if __name__ == "__main__":
    puppet_app = PuppeteerApplication(master_ip="10.0.0.165", puppet_ip="10.0.0.196")
    puppet_app.start_puppeteering()
