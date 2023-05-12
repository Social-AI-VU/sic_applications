import argparse

from sic_framework import SICComponentManager, SICMessage, SICConfMessage, utils
from sic_framework.core.message_python2 import SICRequest
from sic_framework.core.utils import isinstance_pickle
from sic_framework.devices.common_naoqi.nao_motion import NaoMotionActuator

if utils.PYTHON_VERSION_IS_2:
    from naoqi import ALProxy
    import qi


class NaoMotionRecordingStart(SICRequest):
    def __init__(self, tmp):
        super(NaoMotionRecordingStart, self).__init__()
        # TODO improve this by reimplementing parts of the old code
        self.tmp = tmp


class NaoMotionRecordingStop(SICRequest):
    pass


class NaoMotionRecording(SICMessage):
    def __init__(self, motion_recording):
        super(NaoMotionRecording, self).__init__()
        self.motion_recording = motion_recording



class NaoMotionRecorderAction(NaoMotionActuator):
    def __init__(self, *args, **kwargs):
        super(NaoMotionRecorderAction, self).__init__(*args, **kwargs)
        self.is_motion_recording = False

    def stiffness_off(self):
        # "Body" name to signify the collection of all joints
        self.motion.setStiffnesses("Body", 0.0)

    @staticmethod
    def get_inputs():
        return [NaoMotionRecordingStart, NaoMotionRecordingStop]

    @staticmethod
    def get_output():
        return NaoMotionRecording

    def execute(self, motion):

        motion_recording = None

        if isinstance_pickle(motion, NaoMotionRecordingStart):
            """
            Two available commands:
            To start motion recording: 'start;joint_chains;framerate'
            joint_chains = json list of joint names 
            framerate = float
            To stop motion recording: 'stop'
        """
            self.stiffness_off()

            self.process_action_record_motion(motion.tmp)

        if isinstance_pickle(motion, NaoMotionRecordingStop):
            self.logger.critical("STOPPED RECORDING")
            motion_recording = self.process_action_record_motion("stop")

        return NaoMotionRecording(motion_recording)

    def stop(self, *args):
        self.logger.info("Shutdown, setting robot to rest.")
        self.motion.rest()
        super(NaoMotionRecorderAction, self).stop(*args)


class NaoMotionRecordingReplay(SICRequest):
    def __init__(self, motion_recording):
        super(NaoMotionRecordingReplay, self).__init__()
        self.motion_recording = motion_recording


class NaoMotionReplayAction(NaoMotionActuator):
    def __init__(self, *args, **kwargs):
        super(NaoMotionReplayAction, self).__init__(*args, **kwargs)

    def stiffness_on(self):
        # "Body" name to signify the collection of all joints
        self.motion.setStiffnesses("Body", 0.5)

    @staticmethod
    def get_inputs():
        return [NaoMotionRecordingReplay]

    @staticmethod
    def get_output():
        return SICMessage

    def execute(self, motion):
        self.process_action_play_motion(motion.motion_recording)

        return SICMessage()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('robot_name')
    args = parser.parse_args()

    SICComponentManager(NaoMotionRecorderAction, args.robot_name)
