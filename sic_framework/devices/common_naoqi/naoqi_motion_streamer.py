import argparse
import threading

from sic_framework import SICComponentManager, SICMessage, utils, SICRequest, SICConfMessage
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.sensor_python2 import SICSensor
from sic_framework.core.service_python2 import SICService
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionSICv1
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionTools

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class StartStreaming(SICRequest):
    pass


class StopStreaming(SICRequest):
    pass


class NaoJointAngles(SICMessage):
    def __init__(self, joints, angles):
        self.joints = joints
        self.angles = angles


class NaoMotionStreamerConf(SICConfMessage):
    def __init__(self, stiffness=.6):
        """
        :param stiffness: Control how much power the robot should use to reach the given joint angles
        """
        SICConfMessage.__init__(self)
        self.stiffness = stiffness


class NaoMotionStreamerService(SICComponent, NaoqiMotionTools):
    def __init__(self, *args, **kwargs):
        SICComponent.__init__(self, *args, **kwargs)
        NaoqiMotionTools.__init__(self, robot_type="nao")

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.motion = self.session.service('ALMotion')
        self.stiffness = 0

        self.do_streaming = threading.Event()

        self.stream_thread = threading.Thread(target=self.stream_joints)
        self.stream_thread.name = self.get_component_name()
        self.stream_thread.start()

    @staticmethod
    def get_conf():
        return NaoMotionStreamerConf()

    @staticmethod
    def get_inputs():
        return [NaoJointAngles, StartStreaming, StopStreaming]

    def on_request(self, request):
        if request == StartStreaming:
            self.do_streaming.set()
            return SICMessage()

        if request == StartStreaming:
            self.do_streaming.clear()
            return SICMessage()

    def on_message(self, message):
        stiffness = self.params.stiffness

        if self.stiffness != stiffness:
            self.motion.setStiffnesses("Body", stiffness)
            self.stiffness = stiffness

        self.motion.setAngles(message.joints, message.angles, 0.75)

    @staticmethod
    def get_output():
        return NaoJointAngles

    def stream_joints(self):
        # Set the stiffness value of a list of joint chain.
        # For Nao joint chains are: Head, RArm, LArm, RLeg, LLeg

        self.motion.setStiffnesses("Body", 0)

        while not self._stop_event.is_set():

            # check both do_streaming and _stop_event periodically
            self.do_streaming.wait(.5)
            if not self.do_streaming.is_set():
                continue

            joints = self.generate_joint_list(["Body"])

            angles = self.motion.getAngles(joints, False)  # joint_list, use_sensors=True

            self.output_message(NaoJointAngles(joints, angles))




class NaoMotionStreamer(SICConnector):
    component_class = NaoMotionStreamerService

if __name__ == '__main__':
    SICComponentManager([NaoMotionStreamerService])