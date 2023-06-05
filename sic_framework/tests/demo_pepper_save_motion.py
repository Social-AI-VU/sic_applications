import time

from sic_framework.devices.common_naoqi.common_naoqi_motion import NaoqiMotionTools
from sic_framework.devices.common_naoqi.nao_motion import NaoMotion, NaoPostureRequest
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import PepperMotionRecorder, StartRecording, \
    StopRecording, \
    PlayRecording, NaoqiMotionRecorderConf, NaoqiMotionRecording, SetStiffness

conf = NaoqiMotionRecorderConf(use_sensors=True, use_interpolation=True, samples_per_second=60)
recorder = PepperMotionRecorder("192.168.0.148", conf=conf)

motion = NaoMotion(ip="192.168.0.148")

a = NaoPostureRequest("Stand", .5)


# chain = ["Body"] # TODO doesnt work for pepper.

print("Set robot to start position")

chain = ["LArm", "RArm", "Head"]
recorder.request(SetStiffness(0.0, chain))

time.sleep(5)

print("Starting to record in one second!")
time.sleep(1)


recorder.request(StartRecording(chain))

# Lock head while waving, so it doesnt fall
recorder.request(SetStiffness(1.0, ["Head"]))

print("Start moving the robot!")


record_time = 5
time.sleep(record_time)

recording = recorder.request(StopRecording())
recording.save("wave.motion")

print("Done")

time.sleep(2)

print("Replaying action")
# recording = NaoqiMotionRecording.load("wave.motion")

recorder.request(SetStiffness(.95, chain))

recorder.request(PlayRecording(recording))

recorder.request(SetStiffness(.0, chain))


print("end")
