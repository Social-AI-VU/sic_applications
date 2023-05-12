import argparse

from sic_framework import SICComponentManager, SICMessage, utils
from sic_framework.core.sensor_python2 import SICSensor
from sic_framework.core.service_python2 import SICService
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionSICv1
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoJointAngles(SICMessage):
    def __init__(self, joints, angles):
        self.joints = joints
        self.angles = angles


class NaoMotionStreamProducer(SICSensor, NaoqiMotionSICv1):
    def __init__(self, *args, **kwargs):
        SICSensor.__init__(self, *args, **kwargs)
        NaoqiMotionSICv1.__init__(self, robot_type="nao")


        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.motion = self.session.service('ALMotion')
        self.stiffness = 0


    @staticmethod
    def get_inputs():
        return []


    @staticmethod
    def get_output():
        return NaoJointAngles

    def execute(self):
        # Set the stiffness value of a list of joint chain.
        # For Nao joint chains are: Head, RArm, LArm, RLeg, LLeg

        joints = self.generate_joint_list(["Body"])

        self.motion.setStiffnesses("Body", 0)

        angles = self.motion.getAngles(joints, False)  # joint_list, use_sensors=True

        return NaoJointAngles(joints, angles)


class NaoMotionStreamConsumer(SICService, NaoqiMotionSICv1):
    def __init__(self, *args, **kwargs):
        SICService.__init__(self, *args, **kwargs)
        NaoqiMotionSICv1.__init__(self, robot_type="nao")


        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.motion = self.session.service('ALMotion')
        self.stiffness = 0

    @staticmethod
    def get_conf():
        return NaoMotionConf()

    @staticmethod
    def get_inputs():
        return [NaoJointAngles]

    @staticmethod
    def get_output():
        return None

    def execute(self, inputs):
        stiffnes = .6

        motion = inputs[NaoJointAngles.id()]
        if self.stiffness != stiffnes:
            self.motion.setStiffnesses("Body", stiffnes)
            self.stiffness = stiffnes

        self.motion.setAngles(motion.joints, motion.angles, 0.75)

    def stop(self, *args):
        self.logger.info("Shutdown, setting robot to rest.")
        self.motion.rest()
        super(NaoMotionStreamConsumer, self).stop(*args)
