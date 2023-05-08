import json
import threading
from time import sleep

from sic_framework.devices.common_naoqi.motion_affect_transformation import MotionAffectTransformation


PRECISION_FACTOR_MOTION_ANGLES = 1000  # Angle values require a decimal precision of at least 3 (giving a factor of 1000)
PRECISION_FACTOR_MOTION_TIMES = 100  # Time values require a decimal precision of at least 2 (giving a factor of 100)


class NaoqiMotionSICv1(object):

    def __init__(self, robot_type):
        """
        Functions from the previous framework to provide equivalent functionality
        :param robot_type: "nao" or "pepper"
        """
        self.is_motion_recording = False
        self.robot_type = robot_type
        self.motion = None  # INHERITING CLASS MUST SET THIS TO naoqi ALMotion

    ##########################################################################################
    # CODE FROM PREVIOUS SIC FRAMEWORK
    ##########################################################################################
    def process_action_record_motion(self, message):
        """
        Two available commands:
        To start motion recording: 'start;joint_chains;framerate'
        To stop motion recording: 'stop'

        joint_chains: list of joints or joins chains.
        framerate: number of recordings per second

        Suitable joints and joint chains for nao:
        http://doc.aldebaran.com/2-8/family/nao_technical/bodyparts_naov6.html#nao-chains

        Suitable joints and joint chains for pepper:
        http://doc.aldebaran.com/2-5/family/pepper_technical/bodyparts_pep.html

        :param message:
        :return:
        """
        try:
            if 'start' in message:
                _, joint_chains, framerate = message.split(';')
                joint_chains = json.loads(joint_chains)  # parse string json list to python list.
                if not (isinstance(joint_chains, list)):
                    raise ValueError('The supplied joints and chains should be formatted as a list e.g. ["Head", ...].')
                if not self.is_motion_recording:
                    self.is_motion_recording = True
                    self.record_motion_thread = threading.Thread(target=self.record_motion,
                                                                 args=(joint_chains, float(framerate),))
                    self.record_motion_thread.start()
            elif message == 'stop':
                if self.is_motion_recording:
                    self.is_motion_recording = False
                    self.record_motion_thread.join()

                    x = self.compress_motion(self.recorded_motion,
                                             PRECISION_FACTOR_MOTION_ANGLES,
                                             PRECISION_FACTOR_MOTION_TIMES)

                    return x
            else:
                raise ValueError('Command for action_record_motion not recognized: ' + message)
        except ValueError as valerr:
            print(valerr.message)

    def record_motion(self, joint_chains, framerate):
        """
        Helper method for process_action_record_motion that records the angles for a number (framerate) of times
        per second.

        :param joint_chains: list of joints and/or joint chains to record
        :param framerate: number of recordings per second
        :return:
        """
        # get list of joints from chains
        target_joints = self.generate_joint_list(joint_chains)

        # Initialize motion
        motion = {'robot': self.robot_type, 'motion': {}}
        for joint in target_joints:
            motion['motion'][joint] = {}
            motion['motion'][joint]['angles'] = []
            motion['motion'][joint]['times'] = []

        # record motion with a set framerate
        sleep_time = 1.0 / framerate
        time = 0.5  # gives the robot time to move to the start position
        while self.is_motion_recording:
            angles = self.motion.getAngles(target_joints, False)
            for idx, joint in enumerate(target_joints):
                motion['motion'][joint]['angles'].append(angles[idx])
                motion['motion'][joint]['times'].append(time)
            sleep(sleep_time)
            time += sleep_time

        self.recorded_motion = motion


    def process_action_play_motion(self, message, compressed=True):
        """
        Play a motion of a given robot by moving a given set of joints to a given angle for a given time frame.

        :param compressed: flag to indicate whether the motion data is compressed or not
        :param message: compressed json with the following format:
        {'robot': '<nao/pepper>', 'precision_factor_angles': int, 'precision_factor_times': int,
        'motion': {'Joint1': {'angles': list, 'times': list}, 'JointN: {...}}}
        :return:
        """
        try:
            if compressed:
                # get data from message
                data = message.split(';')
                if len(data) == 1:
                    data = NaoqiMotionSICv1.decompress_motion(data[0])
                elif len(data) == 2:
                    transformer = MotionAffectTransformation()
                    data = transformer.transform_label(NaoqiMotionSICv1.decompress_motion(data[0]), data[1])
                elif len(data) == 3:
                    transformer = MotionAffectTransformation()
                    data = transformer.transform_values(NaoqiMotionSICv1.decompress_motion(data[0]), data[1],
                                                        data[2])

                # Extract the the joints, the angles, and the time points from the motion dict.
                if data['robot'] != self.robot_type:
                    raise ValueError('Motion not suitable for ' + self.robot_type)
                motion = data['motion']
            else:
                motion = message

            joints = []
            angles = []
            times = []
            for joint in motion.keys():
                if False:
                    pass
                # if joint == 'LED':  # special case (from emotion transformation)
                #     self.leds.fadeRGB('FaceLeds', int(motion[joint]['colors'][0], 0), motion[joint]['times'][-1])
                #     continue
                # elif joint == 'movement':  # another special case (Pepper movement relay)
                #     movement = motion[joint]['angles']
                #     self.motion.move(movement[0], movement[1], movement[2])
                #     continue
                elif joint not in self.all_joints:
                    print('Joint ' + joint + ' not recognized.')
                    continue

                angls = motion[joint]['angles']
                tms = motion[joint]['times']
                if not angls:
                    print('Joint ' + joint + ' has no angle values')
                elif tms and len(angls) != len(tms):
                    print('The angles list size (' + str(len(angls)) + ') is not equal to ' +
                          'the times list size (' + str(len(tms)) + ') for ' + joint + '.')
                else:
                    joints.append(joint)
                    if tms:
                        angles.append(angls)
                        times.append(tms)
                    else:
                        angles.append(angls[0])

            self.motion.setStiffnesses(joints, 1.0)
            if times:
                self.motion.angleInterpolation(joints, angles, times, True)
            else:
                self.motion.setAngles(joints, angles, 0.75)
        except ValueError as valerr:
            print('action_play_motion received incorrect input: ' + valerr.message)

    def generate_joint_list(self, joint_chains):
        """
        Generates a flat list of valid joints (i.e. present in body_model) from a list of individual joints or joint
        chains for a given robot.

        :param joint_chains:
        :return: list of valid joints
        """
        joints = []
        for joint_chain in joint_chains:
            if joint_chain == 'Body':
                joints += self.all_joints
            elif not joint_chain == 'Body' and joint_chain in self.body_model.keys():
                joints += self.body_model[joint_chain]
            elif joint_chain not in self.body_model.keys() and joint_chain in self.all_joints:
                joints += joint_chain
            else:
                print('Joint ' + joint_chain + ' not recognized. Will be skipped for recording.')
        return joints

    @property
    def body_model(self):
        """
        A list of all the joint chains with corresponding joints for the nao and the pepper.

        For more information see robot documentation:
        For nao: http://doc.aldebaran.com/2-8/family/nao_technical/bodyparts_naov6.html#nao-chains
        For pepper: http://doc.aldebaran.com/2-8/family/pepper_technical/bodyparts_pep.html

        :return:
        """
        body_model = {'nao':
                          {'Body': ['Head', 'LArm', 'LLeg', 'RLeg', 'RArm'],
                           'Head': ['HeadYaw', 'HeadPitch'],
                           'LArm': ['LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll', 'LWristYaw', 'LHand'],
                           'LLeg': ['LHipYawPitch', 'LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'],
                           'RLeg': ['RHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'],
                           'RArm': ['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll', 'RWristYaw',
                                    'RHand']},
                      'pepper':
                          {'Body': ['Head', 'LArm', 'Leg', 'RArm'],
                           'Head': ['HeadYaw', 'HeadPitch'],
                           'LArm': ['LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll', 'LWristYaw', 'LHand'],
                           'Leg': ['HipRoll', 'HipPitch', 'KneePitch'],
                           'RArm': ['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll', 'RWristYaw', 'RHand']}
                      }
        return body_model[self.robot_type]

    @property
    def all_joints(self):
        """
        :return: All joints from body_model for current robot.
        """
        all_joints = []
        for chain in self.body_model['Body']:
            all_joints += self.body_model[chain]
        return all_joints

    @staticmethod
    def compress_motion(motion, precision_factor_angles, precision_factor_times):
        motion['precision_factor_angles'] = precision_factor_angles
        motion['precision_factor_times'] = precision_factor_times
        for joint in motion['motion'].keys():
            motion['motion'][joint]['angles'] = [int(round(a * precision_factor_angles)) for a in
                                                 motion['motion'][joint]['angles']]
            motion['motion'][joint]['times'] = [int(round(t * precision_factor_times)) for t in
                                                motion['motion'][joint]['times']]
        motion = json.dumps(motion, separators=(',', ':'))
        return motion

    @staticmethod
    def decompress_motion(motion):
        motion = json.loads(motion)
        precision_factor_angles = float(motion['precision_factor_angles'])
        precision_factor_times = float(motion['precision_factor_times'])
        for joint in motion['motion'].keys():
            motion['motion'][joint]['angles'] = [float(a / precision_factor_angles) for a in
                                                 motion['motion'][joint]['angles']]
            motion['motion'][joint]['times'] = [float(t / precision_factor_times) for t in
                                                motion['motion'][joint]['times']]
        return motion
