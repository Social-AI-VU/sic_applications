import threading
import time

from sic_framework import SICComponentManager, SICMessage, utils, SICRequest, SICConfMessage
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionTools

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class StartStreaming(SICRequest):
    def __init__(self, joints):
        """
        Start streaming the positions of the selected joints. For more information see robot documentation:
        For nao: http://doc.aldebaran.com/2-8/family/nao_technical/bodyparts_naov6.html#nao-chains
        For pepper: http://doc.aldebaran.com/2-8/family/pepper_technical/bodyparts_pep.html


        :param joints: One of the robot's "Joint chains" such as ["Body"] or ["LArm", "HeadYaw"]
        :type joints: list[str]
        """
        super(StartStreaming, self).__init__()
        self.joints = joints


class StopStreaming(SICRequest):
    pass


class NaoJointAngles(SICMessage):
    def __init__(self, joints, angles):
        self.joints = joints
        self.angles = angles


class NaoMotionStreamerConf(SICConfMessage):
    def __init__(self, stiffness=.6, speed=.75, stream_stiffness=0, use_sensors=False, samples_per_second=20):
        """
        :param stiffness: Control how much power the robot should use to reach the given joint angles
        :param speed: Set the fraction of the maximum speed used to reach the target position.
        :param stream_stiffness: Control the stiffness of the robot when streaming its joint positions.
        Note: Use stiffness, not stream_stiffness,  to control the stiffness of the robot when consuming a stream of
        joint postions.
        :param use_sensors: If true, sensor angles will be returned, otherwise command angles are used.
        :param samples_per_second: How many times per second the joint positions are sampled.
        """
        SICConfMessage.__init__(self)
        self.stiffness = stiffness
        self.speed = speed
        self.stream_stiffness = stream_stiffness
        self.use_sensors = use_sensors
        self.samples_per_second = samples_per_second


class NaoMotionStreamerService(SICComponent, NaoqiMotionTools):
    def __init__(self, *args, **kwargs):
        SICComponent.__init__(self, *args, **kwargs)
        NaoqiMotionTools.__init__(self, robot_type="nao")

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.motion = self.session.service('ALMotion')
        self.stiffness = 0
        self.samples_per_second = self.params.samples_per_second

        self.do_streaming = threading.Event()

        # A list of joint names (not chains)
        self.joints = None

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
            self.joints = self.generate_joint_list(request.joints)
            self.do_streaming.set()
            return SICMessage()

        if request == StartStreaming:
            self.do_streaming.clear()
            return SICMessage()

    def on_message(self, message):

        if self.stiffness != self.params.stiffness:
            self.motion.setStiffnesses(self.joints, self.params.stiffness)
            self.stiffness = self.params.stiffness

        self.motion.setAngles(message.joints, message.angles, self.params.speed)

    @staticmethod
    def get_output():
        return NaoJointAngles

    def stream_joints(self):
        # Set the stiffness value of a list of joint chain.
        # For Nao joint chains are: Head, RArm, LArm, RLeg, LLeg
        try:
            self.motion.setStiffnesses(self.joints, 0)

            while not self._stop_event.is_set():

                # check both do_streaming and _stop_event periodically
                self.do_streaming.wait(.5)
                if not self.do_streaming.is_set():
                    continue

                joints = self.generate_joint_list([self.joints])

                angles = self.motion.getAngles(joints, self.params.use_sensors)  # use_sensors=False

                self.output_message(NaoJointAngles(joints, angles))

                time.sleep(1 / float(self.samples_per_second))
        except Exception as e:
            self.logger.exception(e)
            self.stop()


class NaoMotionStreamer(SICConnector):
    component_class = NaoMotionStreamerService


if __name__ == '__main__':
    SICComponentManager([NaoMotionStreamerService])
