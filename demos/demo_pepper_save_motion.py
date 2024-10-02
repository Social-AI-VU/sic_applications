import time

from sic_framework.devices.common_naoqi.naoqi_motion import NaoqiIdlePostureRequest
from sic_framework.devices.common_naoqi.naoqi_motion_recorder import StartRecording, StopRecording, PlayRecording, NaoqiMotionRecorderConf, NaoqiMotionRecording
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.pepper import Pepper

conf = NaoqiMotionRecorderConf(use_sensors=True, use_interpolation=True, samples_per_second=60)

pepper = Pepper("192.168.0.148", motion_record_conf=conf)




print("Set robot to start position")

chain = ["RArm"]

# Disable "alive" activity for the whole body and set stiffness of the arm to zero
pepper.motion.request(NaoqiIdlePostureRequest("Body", False))
pepper.stiffness.request(Stiffness(0.0, chain))


time.sleep(5)

print("Starting to record in one second!")

time.sleep(1)


pepper.motion_record.request(StartRecording(chain))


print("Start moving the robot!")


record_time = 5
time.sleep(record_time)

recording = pepper.motion_record.request(StopRecording())
recording.save("wave.motion")

print("Done")

time.sleep(2)

print("Replaying action")
# recording = NaoqiMotionRecording.load("wave.motion")

pepper.stiffness.request(Stiffness(.95, chain))

pepper.motion_record.request(PlayRecording(recording))

pepper.stiffness.request(Stiffness(.0, chain))


print("end")
