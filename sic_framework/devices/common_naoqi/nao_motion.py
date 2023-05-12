import argparse
import json
import logging
import threading
from abc import ABCMeta
from threading import Thread
from time import sleep

import six
from sic_framework import SICComponentManager, SICService, utils
import numpy as np
from sic_framework.core.actuator_python2 import SICActuator
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest, SICMessage, SICConfMessage
from sic_framework.core.utils import isinstance_pickle
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionSICv1
from sic_framework.devices.common_naoqi.motion_affect_transformation import MotionAffectTransformation

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoRestRequest(SICRequest):
    """
    Go to the rest position. It is good practise to do this when not using the robot, to allow the motors to cool and
    reduce wear on the robot.
    """
    pass


class NaoWakeUpRequest(SICRequest):
    """
    The robot wakes up: sets Motor on and, if needed, goes to initial position.
    Enable FullyEngaged mode to appear alive.
    """
    pass


class NaoMoveRequest(SICRequest):
    """
    Make the robot move at the given velocity, in the specified direction vector in m/s, where theta indicates rotation.
    x - velocity along X-axis (forward), in meters per second. Use negative values for backward motion
    y - velocity along Y-axis (side), in meters per second. Use positive values to go to the left
    theta - velocity around Z-axis, in radians per second. Use negative values to turn clockwise.
    """
    def __init__(self, x, y, theta):
        super().__init__()
        self.x = x
        self.y = y
        self.theta = theta


class NaoMoveToRequest(NaoMoveRequest):
    """
    Make the robot move to a given point in space relative to the robot, where theta indicates rotation.
    x -  Distance along the X axis (forward) in meters.
    y - Distance along the Y axis (side) in meters.
    theta - Rotation around the Z axis in radians [-3.1415 to 3.1415].
    """
    pass


class NaoMoveTowardRequest(NaoMoveRequest):
    """
    Makes the robot move at the given normalized velocity.
    x - normalized, unitless, velocity along X-axis. +1 and -1 correspond to the maximum velocity in the forward and backward directions, respectively.
    y - normalized, unitless, velocity along Y-axis. +1 and -1 correspond to the maximum velocity in the left and right directions, respectively.
    theta - normalized, unitless, velocity around Z-axis. +1 and -1 correspond to the maximum velocity in the counterclockwise and clockwise directions, respectively.
    """
    pass


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




class NaoMotionActuator(SICActuator, NaoqiMotionSICv1):
    def __init__(self, *args, **kwargs):
        SICActuator.__init__(self, *args, **kwargs)
        NaoqiMotionSICv1.__init__(self, robot_type="nao")

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.animation = self.session.service('ALAnimationPlayer')
        self.awareness = self.session.service('ALBasicAwareness')
        self.motion = self.session.service('ALMotion')
        self.posture = self.session.service('ALRobotPosture')

        self.logger.info("Starting in rest position.")
        self.motion.rest()

        self.stiffness = 0

        self.action_mapping = {
            NaoPostureRequest.id(): self.goToPosture,
            NaoRestRequest.id(): self.rest,
            NaoWakeUpRequest.id(): self.wakeUp,

            NaoMoveRequest.id(): self.move,
            NaoMoveToRequest.id(): self.moveTo,
            NaoMoveTowardRequest.id(): self.moveToward,
        }


    @staticmethod
    def get_inputs():
        return [NaoPostureRequest, NaoRestRequest, NaoWakeUpRequest, NaoMoveRequest, NaoMoveToRequest, 
                NaoMoveTowardRequest]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, input):
        motion = input

        fun = self.action_mapping[motion.id()]

        fun(motion)

        return SICMessage()

    def rest(self, motion):
        self.awareness.stopAwareness()
        self.motion.rest()
        self.stiffness = 0

    def wakeUp(self, motion):
        self.motion.wakeUp()
        self.awareness.setEngagementMode("FullyEngaged")
        self.awareness.startAwareness()

    def goToPosture(self, motion):
        if self.stiffness != .5:
            self.motion.setStiffnesses("Body", .5)
            self.stiffness = .5

        self.posture.goToPosture(motion.target_posture, motion.speed)

    def move(self, motion):
        self.motion.move(motion.x, motion.y, motion.theta)

    def moveTo(self, motion):
        self.motion.moveTo(motion.x, motion.y, motion.theta)

    def moveToward(self, motion):
        self.motion.moveToward(motion.x, motion.y, motion.theta)

    def stop(self, *args):
        self.logger.info("Shutdown, setting robot to rest.")
        self.motion.rest()
        super(NaoMotionActuator, self).stop(*args)

class NaoMotion(SICConnector):
    component_class = NaoMotionActuator

if __name__ == '__main__':
    SICComponentManager([NaoMotionActuator])
