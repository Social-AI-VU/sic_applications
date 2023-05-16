class NaoqiMotionTools(object):

    def __init__(self, robot_type):
        """
        Functions from the previous framework to provide equivalent functionality
        :param robot_type: "nao" or "pepper"
        """
        self.robot_type = robot_type

    def generate_joint_list(self, joint_chains):
        """
        Generates a flat list of valid joints (i.e. present in body_model) from a list of individual joints or joint
        chains for a given robot.

        :param joint_chains:
        :return: list of valid joints
        """
        joints = []
        for joint_chain in joint_chains:
            print(joint_chain)
            if joint_chain == 'Body':
                joints += self.all_joints
            elif not joint_chain == 'Body' and joint_chain in self.body_model.keys():
                joints += self.body_model[joint_chain]
            elif joint_chain not in self.body_model.keys() and joint_chain in self.all_joints:
                joints.append(joint_chain)
            else:
                raise ValueError('Joint {} not recognized.'.format(joint_chain))
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
