import csv
import time

from sic_framework.devices.franka import Franka
from sic_framework.devices.common_franka.franka_motion_recorder import (
    GoHomeRequest,
    PandaJointsRecording,
    PlayRecordingRequest,
    StartRecordingRequest,
    StartTeachingRequest,
    StopRecordingRequest,
    StopTeachingRequest,
)

"""
This demo allows you to enable franka in teaching mode and record the motions you just teach the robot, and replay the motion
To run this demo, you need to install the correct version of the panda-python dependency. A version mismatch will cause problems.
See Installation point 3 for instructions on installing the correct version: https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2412675074/Getting+started+with+Franka+Emika+Research+3#Installation%3A
"""


franka = Franka()

# Make sure the initial pose is home
print("--------first going home--------")

franka.motion_recorder.request(GoHomeRequest())
print("--------Starting teaching mode. Teach the arm for 10 seconds--------")
franka.motion_recorder.request(StartTeachingRequest())

# record for 10 seconds
frequency = 1000
franka.motion_recorder.request(StartRecordingRequest(frequency))
time.sleep(10)

print("--------stop teaching mode--------")
franka.motion_recorder.request(StopTeachingRequest())
joints = franka.motion_recorder.request(StopRecordingRequest())

print("--------going home--------")
franka.motion_recorder.request(GoHomeRequest())


time.sleep(1)
# first replay the teaching joints
print("--------First replay the teaching--------")
franka.motion_recorder.request(PlayRecordingRequest(joints, frequency))

time.sleep(1)
print("--------going home--------")
franka.motion_recorder.request(GoHomeRequest())


# saving the joint pos and vel
motion_file = "joints.motion"
joints.save(motion_file)

# second replay by loadig the motion file we just recorded
time.sleep(1)
loaded_joints = PandaJointsRecording.load(motion_file)
print("--------second replay by loading the motion file we just recorded--------")
franka.motion_recorder.request(PlayRecordingRequest(loaded_joints, frequency))

print("--------Finally going home again--------")
franka.motion_recorder.request(GoHomeRequest())


"""
Optional 1
save binary motion file to csv files for later use
"""

file_1 = "pos.csv"
file_2 = "vel.csv"
# Open a CSV file in write mode
print("--------Saving the joints to csv files--------")
with open(file_1, 'w') as csvfile:
    writer = csv.writer(csvfile)
    for array_str in joints.recorded_joints_pos:
        writer.writerow(array_str)

with open(file_2, 'w') as csvfile:
    writer = csv.writer(csvfile)
    for array_str in joints.recorded_joints_vel:
        writer.writerow(array_str)


"""
Optional 2
load csv file to replay, in case you get the data from somewhere else, pybullet, ros, etc
"""

recorded_joints_pos = []
recorded_joints_vel = []

with open(file_1, 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    for line in csv_reader:
        recorded_joints_pos.append(line)

with open(file_2, 'r') as csvfile:
    csv_reader = csv.reader(csvfile)
    for line in csv_reader:
        recorded_joints_vel.append(line)

print("--------Replaying the joints from csv files and go home--------")
csv_joints = PandaJointsRecording(recorded_joints_pos, recorded_joints_vel)
time.sleep(1)
franka.motion_recorder.request(PlayRecordingRequest(csv_joints))
franka.motion_recorder.request(GoHomeRequest())



