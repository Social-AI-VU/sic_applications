# Franka robot motion and messages
from sic_framework.devices.common_franka.franka_motion import (
    FrankaMotion,
    FrankaPose,
    FrankaPoseRequest,
    FrankaGripperGraspRequest,
    FrankaGripperMoveRequest
)
from sic_framework.devices.franka import Franka

# Desktop and spacemouse input
from sic_framework.devices.common_desktop.desktop_spacemouse import SpaceMouseStates
from sic_framework.devices.desktop import Desktop

import numpy as np
from scipy.spatial.transform import Rotation

"""
This demo allows you to use a space mouse to control the robot arm's end effector (EE),
and demonstrates the mapping between space mouse input and the end effector's displacement

To run this demo, you need to install the correct version of the panda-python dependency. A version mismatch will cause problems.
See Installation point 3 for instructions on installing the correct version: https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2412675074/Getting+started+with+Franka+Emika+Research+3#Installation%3A

Extra installation instruction:
`pip install scipy pyspacemouse`
"""


class MouseStateHandler():
    def __init__(self):
        self.mouse_states = None

    def on_click(self, states):
        self.mouse_states = states
        # print("Mouse states received:", states)

    def on_pose(self, pose):
        # print("Received pose")
        if self.mouse_states is None:
            print("No data received yet from space mouse")
            return
        # convert quaternion to rotation matrix
        initial_rotation_matrix = Rotation.from_quat(pose.orientation).as_matrix()

        # scaling factor for spacemount input
        # smaller values = slower, finer translation; larger = faster, coarser movement
        translation_gain = 0.05  # gain to scale the displacement
        orientation_gain = 0.5  # gain to scale the rotation
        # calculate translation displacement in the end-effector (EE) frame based on SpaceMouse input
        displacement_x = -translation_gain * self.mouse_states.x
        displacement_y = -translation_gain * self.mouse_states.y
        displacement_z = translation_gain * self.mouse_states.z

        # create a transformation matrix for displacement
        T_ee_displacement = np.identity(4)
        T_ee_displacement[0, 3] = displacement_x
        T_ee_displacement[1, 3] = displacement_y
        T_ee_displacement[2, 3] = displacement_z

        # convert into a 4D vector making it compatible with 4x4 T_ee_displacement
        old_position_ee = np.append(pose.position, 1)

        new_ee_pose_4D = np.dot(T_ee_displacement, old_position_ee)
        # extracts the first three elements
        new_ee_pose = new_ee_pose_4D[:3]

        # calculate new rotation angles based on SpaceMouse input, scaling them so each rotation along the axes can reach up to a maximum of ±90 degrees
        angle_x = - np.radians(90) * self.mouse_states.pitch * orientation_gain
        angle_y = - np.radians(90) * self.mouse_states.roll * orientation_gain
        angle_z = np.radians(90) * self.mouse_states.yaw * orientation_gain

        # create a rotation matrix from euler angles
        rotation_matrix_displacement = Rotation.from_euler('xyz', [angle_x, angle_y, angle_z]).as_matrix()

        # calculate new rotation matrix based on spacemouse rotation
        new_rotation_matrix = np.dot(initial_rotation_matrix, rotation_matrix_displacement)

        # convert new rotation matrix back to a quaternion
        new_quaternion = Rotation.from_matrix(new_rotation_matrix).as_quat()

        franka.motion.send_message(FrankaPose(position=new_ee_pose, orientation=new_quaternion))

        # gripper control: left button to close, right button to open
        if self.mouse_states.buttons[0] == 1:
            franka.motion.request(FrankaGripperGraspRequest(width=0.0, speed=0.1, force=5, epsilon_inner=0.005, epsilon_outer=0.005))
        if self.mouse_states.buttons[1] == 1:
            franka.motion.request(FrankaGripperMoveRequest(width=0.08, speed=0.1))

mouse_handler = MouseStateHandler()
desktop = Desktop()
franka = Franka()

desktop.spacemouse.register_callback(callback=mouse_handler.on_click)
franka.motion.register_callback(callback=mouse_handler.on_pose)

franka.motion.request(FrankaPoseRequest(stream=True))
