import threading
import time

import numpy as np

from sic_framework import SICComponentManager, SICMessage, utils, SICActuator
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest, SICConfMessage
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionTools

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class StartRecording(SICRequest):
    def __init__(self, joints):
        """
        Record motion of the selected joints. For more information see robot documentation:
        For nao: http://doc.aldebaran.com/2-8/family/nao_technical/bodyparts_naov6.html#nao-chains
        For pepper: http://doc.aldebaran.com/2-8/family/pepper_technical/bodyparts_pep.html


        :param joints: One of the robot's "Joint chains" such as ["Body"] or ["LArm", "HeadYaw"]
        :type joints: list[str]
        """
        super(StartRecording, self).__init__()
        self.joints = joints


class StopRecording(SICRequest):
    pass


class NaoMotionRecording(SICMessage):
    def __init__(self, recorded_joints, recorded_angles, recorded_times):
        """
        A recording of the robot's motion.

        Example data:
        recorded_joints = ["HeadYaw", "HeadPitch", "LWrist"]
        recorded_angles = [ [.13, .21, .25],   # angles in radians for HeadYaw
                            [.21, .23, .31],   # HeadPitch
                            [.-1, .0,  .1],   # LWrist
                          ]
        recorded_times  = [ [.1, .2, .3],   # time in seconds for when angle should be reached for HeadYaw
                            [.1, .2, .3],   # HeadPitch
                            [.1, .2, .3],   # LWrist
                          ]
        See http://doc.aldebaran.com/2-1/naoqi/motion/control-joint-api.html#joint-control-api
        For more examples regarding angleInterpolation() API

        :param recorded_joints: List of joints (joints like "HeadYaw", not chains such as "Body")
        :param recorded_angles:
        :param recorded_times:
        """
        super(NaoMotionRecording, self).__init__()
        self.recorded_joints = recorded_joints
        self.recorded_angles = recorded_angles
        self.recorded_times = recorded_times


class PlayRecording(SICRequest):
    def __init__(self, motion_recording_message):
        """
        Play a recorded motion.
        :param motion_recording_message: a NaoMotionRecording message

        """
        super(PlayRecording, self).__init__()
        self.motion_recording_message = motion_recording_message


class NaoMotionRecorderConf(SICConfMessage):
    def __init__(self, replay_stiffness=.6, replay_speed=.75, use_interpolation=True, setup_time=.5, use_sensors=False):
        """
        There is a choice between setAngles, which is an approximation of the motion or
        angleInterpolation which may not play the motion if it exceeds max body speed.

        Note replay_speed is only used for use_interpolation=False.
        Note setup_time is only used for use_interpolation=True.

        :param replay_stiffness: Control how much power the robot should use to reach the given joint angles.
        :param replay_speed: Control how fast the robot should to reach the given joint angles. Only used if
                             use_interpolation=False
        :param use_interpolation: Use setAngles if False and angleInterpolation if True.
        :param setup_time: The time in seconds the robot has to reach the start position of the recording. Only used
                           when use_interpolation=True.
        :param use_sensors: If true, sensor angles will be returned, otherwise command angles are used.
        """
        SICConfMessage.__init__(self)
        self.replay_stiffness = replay_stiffness
        self.replay_speed = replay_speed
        self.use_interpolation = use_interpolation
        self.setup_time = setup_time
        self.use_sensors = use_sensors


class NaoMotionRecorderActuator(SICActuator, NaoqiMotionTools):
    def __init__(self, *args, **kwargs):
        SICActuator.__init__(self, *args, **kwargs)
        NaoqiMotionTools.__init__(self, robot_type="nao")

        self.session = qi.Session()
        self.session.connect('tcp://127.0.0.1:9559')

        self.motion = self.session.service('ALMotion')

        self.recorded_joints = []
        self.recorded_angles = []
        self.recorded_times = []

        self.do_recording = threading.Event()
        self.record_start_time = None

        # A list of joint names (not chains)
        self.joints = None

        self.stream_thread = threading.Thread(target=self.record_motion)
        self.stream_thread.name = self.get_component_name()
        self.stream_thread.start()

        self.samples_per_second = 20

    @staticmethod
    def get_conf():
        return NaoMotionRecorderConf()

    @staticmethod
    def get_inputs():
        return [StartRecording, StopRecording]

    @staticmethod
    def get_output():
        return NaoMotionRecording

    def record_motion(self):
        """

        :param joint_chains: list of joints and/or joint chains to record
        :param framerate: number of recordings per second
        :return:
        """
        try:

            while not self._stop_event.is_set():

                # check both do_recording and _stop_event periodically
                self.do_recording.wait(1)
                if not self.do_recording.is_set():
                    continue

                angles = self.motion.getAngles(self.joints, self.params.use_sensors)
                time_delta = time.time() - self.record_start_time

                for joint_idx, angle in enumerate(angles):
                    self.recorded_angles[joint_idx].append(angle)
                    self.recorded_times[joint_idx].append(time_delta)

                time.sleep(1 / float(self.samples_per_second))


        except Exception as e:
            self.logger.exception(e)
            self.stop()

    def reset_recording_variables(self, request):
        """
        Initialize variables that will be populated during recording.
        :param request:
        """
        self.record_start_time = time.time()
        print("request.joints:", request.joints)
        self.joints = self.generate_joint_list(request.joints)
        print("Joint list:", self.joints)
        self.recorded_angles = []
        self.recorded_times = []
        for _ in self.joints:
            self.recorded_angles.append([])
            self.recorded_times.append([])

    def execute(self, request):
        if request == StartRecording:
            self.reset_recording_variables(request)
            self.motion.setStiffnesses(self.joints, 0.0)

            self.do_recording.set()
            return SICMessage()

        if request == StopRecording:
            self.do_recording.clear()
            return NaoMotionRecording(self.joints, self.recorded_angles, self.recorded_times)

        if request == PlayRecording:
            self.motion.setStiffnesses(self.joints, self.params.replay_stiffness)
            return self.replay_recording(request)

    def replay_recording(self, request):
        message = request.motion_recording_message

        joints = message.recorded_joints
        angles = message.recorded_angles
        times = message.recorded_times

        if self.params.use_interpolation:
            times = np.array(times) + self.params.setup_time
            times = times.tolist()
            self.motion.angleInterpolation(joints, angles, times, True)  # isAbsolute = bool

        else:
            # compute the average time delta (should be 1 / self.samples_per_second anyway)
            sleep_time = max(times[0]) / len(times[0])

            for a in np.array(angles).T.tolist():
                self.motion.setAngles(joints, a, self.params.replay_speed)
                time.sleep(sleep_time)

        return SICMessage()

    def stop(self, *args):
        self.logger.info("Shutdown, setting robot to rest.")
        self.motion.rest()
        super(NaoMotionRecorderActuator, self).stop(*args)


class NaoMotionRecorder(SICConnector):
    component_class = NaoMotionRecorderActuator


if __name__ == '__main__':
    # SICComponentManager([NaoMotionRecorderActuator])
    a = NaoMotionRecorderActuator()
    a._start()
