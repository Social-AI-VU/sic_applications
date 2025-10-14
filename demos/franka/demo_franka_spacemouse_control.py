# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.franka import Franka
from sic_framework.devices.desktop import Desktop

# Import message types and requests
from sic_framework.devices.common_franka.franka_motion import (
    FrankaMotion,
    FrankaPose,
    FrankaPoseRequest,
    FrankaGripperGraspRequest,
    FrankaGripperMoveRequest
)
from sic_framework.devices.common_desktop.desktop_spacemouse import SpaceMouseStates

# Import libraries necessary for the demo
import numpy as np
from scipy.spatial.transform import Rotation


class MouseStateHandler:
    """Handler for processing space mouse input and converting to robot motion."""
    
    def __init__(self, franka, logger):
        self.franka = franka
        self.logger = logger
        self.mouse_states = None
        
        # Scaling factors for spacemouse input
        # Smaller values = slower, finer translation; larger = faster, coarser movement
        self.translation_gain = 0.05
        self.orientation_gain = 0.5
        self.deadzone_threshold = 0.05

    def on_click(self, states):
        """Callback for space mouse state updates."""
        self.mouse_states = states

    def on_pose(self, pose):
        """Callback for Franka pose updates - computes new pose based on space mouse input."""
        if self.mouse_states is None:
            self.logger.debug("No data received yet from space mouse")
            return
        
        # Convert quaternion to rotation matrix
        initial_rotation_matrix = Rotation.from_quat(pose.orientation).as_matrix()

        # Apply deadzone to translation inputs to avoid small jitters
        x = self.mouse_states.x if abs(self.mouse_states.x) > self.deadzone_threshold else 0.0
        y = self.mouse_states.y if abs(self.mouse_states.y) > self.deadzone_threshold else 0.0
        z = self.mouse_states.z if abs(self.mouse_states.z) > self.deadzone_threshold else 0.0

        # Calculate translation displacement in the end-effector (EE) frame
        displacement_x = -self.translation_gain * x
        displacement_y = -self.translation_gain * y
        displacement_z = self.translation_gain * z

        # Create a transformation matrix for displacement
        T_ee_displacement = np.identity(4)
        T_ee_displacement[0, 3] = displacement_x
        T_ee_displacement[1, 3] = displacement_y
        T_ee_displacement[2, 3] = displacement_z

        # Convert into a 4D vector making it compatible with 4x4 T_ee_displacement
        old_position_ee = np.append(pose.position, 1)
        new_ee_pose_4D = np.dot(T_ee_displacement, old_position_ee)
        new_ee_pose = new_ee_pose_4D[:3]  # Extract the first three elements

        # Apply deadzone to orientation inputs
        pitch = self.mouse_states.pitch if abs(self.mouse_states.pitch) > self.deadzone_threshold else 0.0
        roll = self.mouse_states.roll if abs(self.mouse_states.roll) > self.deadzone_threshold else 0.0
        yaw = self.mouse_states.yaw if abs(self.mouse_states.yaw) > self.deadzone_threshold else 0.0

        # Calculate new rotation angles based on SpaceMouse input
        angle_x = -np.radians(90) * pitch * self.orientation_gain
        angle_y = -np.radians(90) * roll * self.orientation_gain
        angle_z = np.radians(90) * yaw * self.orientation_gain

        # Create a rotation matrix from euler angles
        rotation_matrix_displacement = Rotation.from_euler('xyz', [angle_x, angle_y, angle_z]).as_matrix()

        # Calculate new rotation matrix based on spacemouse rotation
        new_rotation_matrix = np.dot(initial_rotation_matrix, rotation_matrix_displacement)

        # Convert new rotation matrix back to a quaternion
        new_quaternion = Rotation.from_matrix(new_rotation_matrix).as_quat()

        # Send new pose to Franka
        self.franka.motion.send_message(FrankaPose(position=new_ee_pose, orientation=new_quaternion))

        # Gripper control: left button to close, right button to open
        if self.mouse_states.buttons[0] == 1:
            self.franka.motion.request(
                FrankaGripperGraspRequest(
                    width=0.0, speed=0.1, force=5,
                    epsilon_inner=0.005, epsilon_outer=0.005
                )
            )
        if self.mouse_states.buttons[1] == 1:
            self.franka.motion.request(FrankaGripperMoveRequest(width=0.08, speed=0.1))


class FrankaSpacemouseDemo(SICApplication):
    """
    Franka spacemouse control demo application.
    Demonstrates using a space mouse to control the robot arm's end effector.

    IMPORTANT:
    To run this demo, you need to install the correct version of the panda-python dependency.
    A version mismatch will cause problems.
    See Installation point 3 for instructions:
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2412675074/Getting+started+with+Franka+Emika+Research+3#Installation%3A

    Extra installation:
    pip install scipy pyspacemouse
    """
    
    def __init__(self, log_level=sic_logging.INFO):
        # Call parent constructor (handles singleton initialization)
        super(FrankaSpacemouseDemo, self).__init__(log_level=log_level)
        
        # Demo-specific initialization
        self.franka = None
        self.desktop = None
        self.mouse_handler = None
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/franka/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the Franka robot and Desktop spacemouse."""
        self.logger.info("Starting Franka Spacemouse Control Demo...")
        
        # Initialize devices
        self.desktop = Desktop()
        self.franka = Franka()
        
        # Create mouse state handler
        self.mouse_handler = MouseStateHandler(self.franka, self.logger)
        
        # Register callbacks
        self.desktop.spacemouse.register_callback(callback=self.mouse_handler.on_click)
        self.franka.motion.register_callback(callback=self.mouse_handler.on_pose)
        
        # Start pose streaming
        self.franka.motion.request(FrankaPoseRequest(stream=True))
    
    def run(self):
        """Main application loop."""
        self.logger.info("Spacemouse control active. Use the space mouse to control the robot.")
        self.logger.info("Left button: close gripper, Right button: open gripper")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while not self.shutdown_event.is_set():
                pass  # Keep running until interrupted
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = FrankaSpacemouseDemo()
    demo.run()

