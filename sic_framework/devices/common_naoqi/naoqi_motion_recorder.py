import argparse
import threading
import time

from sic_framework import SICComponentManager, SICMessage, SICConfMessage, utils, SICActuator
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICRequest
from sic_framework.core.utils import isinstance_pickle
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionSICv1
from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionTools
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class StartRecording(SICRequest):
    def __init__(self, joints):
        super(StartRecording, self).__init__()
        self.joints = joints


class StopRecording(SICRequest):
    pass


class NaoMotionRecording(SICMessage):
    def __init__(self, recorded_joints, recorded_angles, recorded_times):
        super(NaoMotionRecording, self).__init__()
        self.recorded_joints = recorded_joints
        self.recorded_angles = recorded_angles
        self.recorded_times = recorded_times


class PlayRecording(SICRequest):
    def __init__(self, motion_recording_message):
        super(PlayRecording, self).__init__()
        self.motion_recording_message = motion_recording_message


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
        self.joints = None

        self.stream_thread = threading.Thread(target=self.record_motion)
        self.stream_thread.name = self.get_component_name()
        self.stream_thread.start()

    def stiffness_off(self):
        # TODO add stiffness controls?
        # "Body" name to signify the collection of all joints
        self.motion.setStiffnesses("Body", 0.0)

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

        while not self._stop_event.is_set():

            # check both do_recording and _stop_event periodically
            self.do_recording.wait(.5)
            if not self.do_recording.is_set():
                continue

            angles = self.motion.getAngles(self.joints, use_sensors=False)
            times = time.time() - self.record_start_time

            self.recorded_joints.append(self.joints)
            self.recorded_angles.append(angles)
            self.recorded_times.append(times)

    def execute(self, request):
        if request == StartRecording:
            self.record_start_time = time.time()
            self.do_recording.set()
            self.recorded_joints = []
            self.recorded_angles = []
            self.recorded_times = []
            self.joints = request.joints

            return SICMessage()

        if request == StopRecording:
            self.do_recording.clear()
            return NaoMotionRecording(self.recorded_joints, self.recorded_angles, self.recorded_times)

        if request == PlayRecording:
            return self.replay_recording(request)

    def replay_recording(self, request):
        message = request.motion_recording_message

        joints = message.joints
        angles = message.angles
        times  = message.times
        
        self.motion.angleInterpolation(joints, angles, times, isAbsolute=True)
        return SICMessage()

    def stop(self, *args):
        self.logger.info("Shutdown, setting robot to rest.")
        self.motion.rest()
        super(NaoMotionRecorderActuator, self).stop(*args)


class NaoMotionRecorder(SICConnector):
    component_class = NaoMotionRecorderActuator

if __name__ == '__main__':
    SICComponentManager([NaoMotionRecorderActuator])