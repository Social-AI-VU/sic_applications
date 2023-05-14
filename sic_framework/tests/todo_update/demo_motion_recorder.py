import logging
import time

from sic_framework.core.connector import SICApplication
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import NaoMotionRecorderActuator, NaoMotionReplayAction, \
    NaoMotionRecordingStart, NaoMotionRecordingStop, NaoMotionRecordingReplay

""" This demo should display a camera image
"""


class DemoMotion(SICApplication):

    def run(self) -> None:
        #### use camera

        recorder = self.start_service(NaoMotionRecorderActuator, device_id='nao', inputs_to_service=[self],
                                      log_level=logging.INFO)
        replay_action = self.start_service(NaoMotionReplayAction, device_id='nao', inputs_to_service=[self],
                                           log_level=logging.INFO)

        recorder.request(NaoMotionRecordingStart('start;["Body"];20'))
        print("Start moving the head!")

        record_time = 15

        time.sleep(record_time)

        recording = recorder.request(NaoMotionRecordingStop())
        print("Done")

        print("Replaying action")

        req_recording = NaoMotionRecordingReplay(recording.motion_recording)
        replay_action.request(req_recording, timeout=record_time + 5)

        time.sleep(record_time)
        print("end")


if __name__ == '__main__':
    test_app = DemoMotion()

    test_app.run()
    test_app.stop()

"""
Robot exports

export DB_PASS=changemeplease
export DB_SSL_SELFSIGNED=1
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/sic/core/lib/libtubojpeg/lib32/
export DB_IP=192.168.0.FOO
"""
