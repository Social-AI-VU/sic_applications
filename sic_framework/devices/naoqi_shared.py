from __future__ import print_function

import threading
import time

from sic_framework.core import sic_redis, utils
from sic_framework.core.utils import MAGIC_STARTED_COMPONENT_MANAGER_TEXT
from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoqiAutonomousActuator, NaoqiAutonomous
from sic_framework.devices.common_naoqi.naoqi_leds import NaoqiLEDs, \
    NaoqiLEDsActuator
from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiMotionActuator, NaoqiMotion
from sic_framework.devices.common_naoqi.naoqi_camera import NaoqiTopCameraSensor, \
    NaoqiBottomCameraSensor, NaoqiTopCamera, \
    NaoqiBottomCamera
from sic_framework.devices.common_naoqi.naoqi_microphone import \
    NaoqiMicrophone, NaoqiMicrophoneSensor
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoqiMotionRecorderActuator, NaoqiMotionRecorder
from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoqiMotionStreamerService, NaoqiMotionStreamer
from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiSpeakerComponent, NaoqiSpeaker
from sic_framework.devices.common_naoqi.naoqi_stiffness import NaoqiStiffnessActuator, NaoqiStiffness
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import \
    NaoqiTextToSpeechActuator, NaoqiTextToSpeech
from sic_framework.devices.device import SICDevice
from abc import ABCMeta

shared_naoqi_components = [
    NaoqiTopCameraSensor,
    NaoqiBottomCameraSensor,
    NaoqiMicrophoneSensor,
    NaoqiMotionActuator,
    NaoqiTextToSpeechActuator,
    NaoqiMotionRecorderActuator,
    NaoqiMotionStreamerService,
    NaoqiStiffnessActuator,
    NaoqiAutonomousActuator,
    NaoqiLEDsActuator,
    NaoqiSpeakerComponent,
]


class Naoqi(SICDevice):
    __metaclass__ = ABCMeta

    def __init__(self, ip,
                 robot_type,
                 top_camera_conf=None,
                 bottom_camera_conf=None,
                 mic_conf=None,
                 motion_conf=None,
                 tts_conf=None,
                 motion_record_conf=None,
                 motion_stream_conf=None,
                 stiffness_conf=None,
                 speaker_conf=None,
                 username=None, passwords=None,
                 ):
        super().__init__(ip, username=username, passwords=passwords, )

        # Set the component configs

        self.configs[NaoqiTopCamera] = top_camera_conf
        self.configs[NaoqiBottomCamera] = bottom_camera_conf
        self.configs[NaoqiMicrophone] = mic_conf
        self.configs[NaoqiMotion] = motion_conf
        self.configs[NaoqiTextToSpeech] = tts_conf
        self.configs[NaoqiMotionRecorder] = motion_record_conf
        self.configs[NaoqiMotionStreamer] = motion_stream_conf
        self.configs[NaoqiStiffness] = stiffness_conf
        self.configs[NaoqiSpeaker] = speaker_conf

        assert robot_type in ["nao", "pepper"], "Robot type must be either 'nao' or 'pepper'"

        self.auto_install()

        redis_hostname, _ = sic_redis.get_redis_db_ip_password()

        if redis_hostname == "127.0.0.1" or redis_hostname == "localhost":
            # get own public ip address for the device to use
            redis_hostname = utils.get_ip_adress()

        stop_cmd = """
                pkill -f "python2 {}.py"
                """.format(robot_type)

        start_cmd = """
                export PYTHONPATH=/opt/aldebaran/lib/python2.7/site-packages; \
                export LD_LIBRARY_PATH=/opt/aldebaran/lib/naoqi; \
                cd ~/framework/sic_framework/devices; \
                echo 'Robot: Starting SIC';\
                python2 {robot_type}.py --redis_ip={redis_host}; 
                """.format(robot_type=robot_type, redis_host=redis_hostname)

        self.ssh.exec_command(stop_cmd)
        time.sleep(.1)

        # on_windows = sys.platform == 'win32'
        # use_pty = not on_windows

        stdin, stdout, _ = self.ssh.exec_command(start_cmd, get_pty=False)
        # merge stderr to stdout to simplify (and prevent potential deadlock as stderr is not read)
        stdout.channel.set_combine_stderr(True)

        print("Starting SIC on {} with redis ip {}".format(robot_type, redis_hostname))
        self.logfile = open("sic.log", "w")

        # Set up error monitoring
        def check_if_exit():
            # wait for the process to exit
            status = stdout.channel.recv_exit_status()
            # if remote threads exits before local main thread, report to user.
            if threading.main_thread().is_alive():
                raise RuntimeError("Remote SIC program has stopped unexpectedly.\nSee sic.log for details")

        thread = threading.Thread(target=check_if_exit, daemon=True)
        thread.name = "remote_SIC_process_monitor"
        thread.start()

        # wait for 3 seconds for SIC to start
        for i in range(300):
            line = stdout.readline()
            self.logfile.write(line)

            if MAGIC_STARTED_COMPONENT_MANAGER_TEXT in line:
                break
            time.sleep(.01)
        else:
            raise RuntimeError("Could not start SIC on remote device\nSee sic.log for details")

        # write the remaining output to the logfile
        def write_logs():
            for line in stdout:
                self.logfile.write(line)

        thread = threading.Thread(target=write_logs, daemon=True)
        thread.name = "remote_SIC_process_log_writer"
        thread.start()

    @property
    def top_camera(self):
        return self._get_connector(NaoqiTopCamera)

    @property
    def bottom_camera(self):
        return self._get_connector(NaoqiBottomCamera)

    @property
    def mic(self):
        return self._get_connector(NaoqiMicrophone)

    @property
    def motion(self):
        return self._get_connector(NaoqiMotion)

    @property
    def tts(self):
        return self._get_connector(NaoqiTextToSpeech)

    @property
    def motion_record(self):
        return self._get_connector(NaoqiMotionRecorder)

    @property
    def motion_streaming(self):
        return self._get_connector(NaoqiMotionStreamer)

    @property
    def stiffness(self):
        return self._get_connector(NaoqiStiffness)

    @property
    def autonomous(self):
        return self._get_connector(NaoqiAutonomous)

    @property
    def leds(self):
        return self._get_connector(NaoqiLEDs)

    @property
    def speaker(self):
        return self._get_connector(NaoqiSpeaker)

    def __del__(self):
        self.logfile.close()


if __name__ == "__main__":
    pass
