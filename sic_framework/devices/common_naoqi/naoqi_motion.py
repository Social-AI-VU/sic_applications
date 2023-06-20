import six
from sic_framework import SICComponentManager, SICService, utils
import numpy as np
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest, SICMessage, SICConfMessage

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoqiMoveRequest(SICRequest):
    """
    Make the robot move at the given velocity, in the specified direction vector in m/s, where theta indicates rotation.
    x - velocity along X-axis (forward), in meters per second. Use negative values for backward motion
    y - velocity along Y-axis (side), in meters per second. Use positive values to go to the left
    theta - velocity around Z-axis, in radians per second. Use negative values to turn clockwise.
    """

    def __init__(self, x, y, theta):
        super(NaoqiMoveRequest, self).__init__()
        self.x = x
        self.y = y
        self.theta = theta


class NaoqiMoveToRequest(NaoqiMoveRequest):
    """
    Make the robot move to a given point in space relative to the robot, where theta indicates rotation.
    x -  Distance along the X axis (forward) in meters.
    y - Distance along the Y axis (side) in meters.
    theta - Rotation around the Z axis in radians [-3.1415 to 3.1415].
    """
    pass


class NaoqiMoveTowardRequest(NaoqiMoveRequest):
    """
    Makes the robot move at the given normalized velocity.
    x - normalized, unitless, velocity along X-axis. +1 and -1 correspond to the maximum velocity in the forward and backward directions, respectively.
    y - normalized, unitless, velocity along Y-axis. +1 and -1 correspond to the maximum velocity in the left and right directions, respectively.
    theta - normalized, unitless, velocity around Z-axis. +1 and -1 correspond to the maximum velocity in the counterclockwise and clockwise directions, respectively.
    """
    pass


class NaoqiIdlePostureRequest(SICRequest):
    def __init__(self, joints, value):
        """
        Control idle behaviour
        http://doc.aldebaran.com/2-4/naoqi/motion/idle.html
        :param joints: The chain name, one of ["Body", "Legs", "Arms", "LArm", "RArm" or "Head"].
        :type joints: str
        :param value: True or False
        :type value: bool
        """
        super(NaoqiIdlePostureRequest, self).__init__()
        self.joints = joints
        self.value = value


class NaoqiBreathingRequest(SICRequest):
    def __init__(self, joints, value):
        """
        Control Breathing behaviour
        http://doc.aldebaran.com/2-4/naoqi/motion/idle.html
        :param joints: The chain name, one of ["Body", "Legs", "Arms", "LArm", "RArm" or "Head"].
        :type joints: str
        :param value: True or False
        :type value: bool
        """
        super(NaoqiBreathingRequest, self).__init__()
        self.joints = joints
        self.value = value


class NaoPostureRequest(SICRequest):
    """
    Make the robot go to a predefined posture.
    Options:
    ["Crouch", "LyingBack" "LyingBelly", "Sit", "SitRelax", "Stand", "StandInit", "StandZero"]
    """

    def __init__(self, target_posture, speed=.4):
        super(NaoPostureRequest, self).__init__()
        options = ["Crouch", "LyingBack" "LyingBelly", "Sit", "SitRelax", "Stand", "StandInit", "StandZero"]
        assert target_posture in options, "Invalid pose {}".format(target_posture)
        self.target_posture = target_posture
        self.speed = speed


class NaoqiAnimationRequest(SICRequest):
    """
    Make the robot play predefined animation. Either the short or full name as a string will work.
    See: http://doc.aldebaran.com/2-4/naoqi/motion/alanimationplayer-advanced.html#animationplayer-list-behaviors-nao

    Nao Examples:
        animations/Sit/BodyTalk/BodyTalk_1
        animations/Stand/Gestures/Hey_1
        Enthusiastic_4

    Pepper Examples:
        Hey_3
        animations/Stand/Gestures/ShowSky_5
    """

    def __init__(self, animation_path):
        """
        :param animation_path: the animation name or path
        :type animation_path: str
        """
        super(NaoqiAnimationRequest, self).__init__()
        self.animation_path = animation_path


class PepperPostureRequest(SICRequest):
    """
    Make the robot go to a predefined posture.
    Options:
    ["Crouch", "LyingBack" "LyingBelly", "Sit", "SitRelax", "Stand", "StandInit", "StandZero"]
    """

    def __init__(self, target_posture, speed=.4):
        super(PepperPostureRequest, self).__init__()
        options = ["Crouch", "Stand", "StandInit", "StandZero"]
        assert target_posture in options, "Invalid pose {}".format(target_posture)
        self.target_posture = target_posture
        self.speed = speed


class NaoqiMotionActuator(SICActuator):
    def __init__(self, *args, **kwargs):
        SICActuator.__init__(self, *args, **kwargs)

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.motion = self.session.service('ALMotion')
        self.posture = self.session.service('ALRobotPosture')
        self.animation = self.session.service("ALAnimationPlayer")

    @staticmethod
    def get_inputs():
        return [NaoPostureRequest, NaoqiMoveRequest, NaoqiMoveToRequest, NaoqiMoveTowardRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, request):
        motion = request

        if motion == NaoPostureRequest:
            self.goToPosture(motion)
        if motion == NaoqiAnimationRequest:
            self.run_animation(motion)
        elif motion == NaoqiIdlePostureRequest:
            self.motion.setIdlePostureEnabled(motion.joints, motion.value)
        elif motion == NaoqiBreathingRequest:
            self.motion.setBreathEnabled(motion.joints, motion.value)

        elif motion == NaoqiMoveRequest:
            self.move(motion)
        elif motion == NaoqiMoveToRequest:
            self.moveTo(motion)
        elif motion == NaoqiMoveTowardRequest:
            self.moveToward(motion)

        return SICMessage()

    def goToPosture(self, motion):
        self.posture.goToPosture(motion.target_posture, motion.speed)

    def run_animation(self, motion):
        self.animation.run(motion.animation_path)

    def move(self, motion):
        self.motion.move(motion.x, motion.y, motion.theta)

    def moveTo(self, motion):
        self.motion.moveTo(motion.x, motion.y, motion.theta)

    def moveToward(self, motion):
        self.motion.moveToward(motion.x, motion.y, motion.theta)


class NaoqiMotion(SICConnector):
    component_class = NaoqiMotionActuator


if __name__ == '__main__':
    SICComponentManager([NaoqiMotionActuator])
