# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.franka import Franka

# Import message types and requests
from sic_framework.devices.common_franka.franka_motion_recorder import (
    GoHomeRequest,
    PandaJointsRecording,
    PlayRecordingRequest,
    StartRecordingRequest,
    StartTeachingRequest,
    StopRecordingRequest,
    StopTeachingRequest,
)

# Import libraries necessary for the demo
import csv
import time


class FrankaMotionRecorderDemo(SICApplication):
    """
    Franka motion recorder demo application.
    Demonstrates enabling Franka in teaching mode, recording motions, and replaying them.
    
    IMPORTANT:
    To run this demo, you need to install the correct version of the panda-python dependency.
    A version mismatch will cause problems.
    See Installation point 3 for instructions:
    https://socialrobotics.atlassian.net/wiki/spaces/CBSR/pages/2412675074/Getting+started+with+Franka+Emika+Research+3#Installation%3A
    """
    
    def __init__(self, motion_file="joints.motion", record_time=10, frequency=1000, log_level=sic_logging.INFO):
        # Call parent constructor (handles singleton initialization)
        super(FrankaMotionRecorderDemo, self).__init__(log_level=log_level)
        
        # Demo-specific initialization
        self.motion_file = motion_file
        self.record_time = record_time
        self.frequency = frequency
        self.franka = None
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/franka/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the Franka robot."""
        self.logger.info("Starting Franka Motion Recorder Demo...")
        
        # Initialize Franka robot
        self.franka = Franka()
    
    def run(self):
        """Main application logic."""
        try:
            # Make sure the initial pose is home
            self.logger.info("First going home")
            self.franka.motion_recorder.request(GoHomeRequest())
            
            self.logger.info("Starting teaching mode. Teach the arm for {} seconds".format(self.record_time))
            self.franka.motion_recorder.request(StartTeachingRequest())
            
            # Record for specified time
            self.franka.motion_recorder.request(StartRecordingRequest(self.frequency))
            time.sleep(self.record_time)
            
            self.logger.info("Stop teaching mode")
            self.franka.motion_recorder.request(StopTeachingRequest())
            joints = self.franka.motion_recorder.request(StopRecordingRequest())
            
            self.logger.info("Going home")
            self.franka.motion_recorder.request(GoHomeRequest())
            
            time.sleep(1)
            # First replay the teaching joints
            self.logger.info("First replay the teaching")
            self.franka.motion_recorder.request(PlayRecordingRequest(joints, self.frequency))
            
            time.sleep(1)
            self.logger.info("Going home")
            self.franka.motion_recorder.request(GoHomeRequest())
            
            # Save the joint pos and vel
            self.logger.info("Saving motion to file: {}".format(self.motion_file))
            joints.save(self.motion_file)
            
            # Second replay by loading the motion file we just recorded
            time.sleep(1)
            loaded_joints = PandaJointsRecording.load(self.motion_file)
            self.logger.info("Second replay by loading the motion file")
            self.franka.motion_recorder.request(PlayRecordingRequest(loaded_joints, self.frequency))
            
            self.logger.info("Finally going home again")
            self.franka.motion_recorder.request(GoHomeRequest())
            
            # Optional: Save to CSV files
            self._save_to_csv(joints)
            
            # Optional: Replay from CSV files
            self._replay_from_csv()
            
            self.logger.info("Motion recorder demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()
    
    def _save_to_csv(self, joints):
        """
        Optional: Save binary motion file to CSV files for later use.
        
        Args:
            joints: The recorded joints to save.
        """
        file_pos = "pos.csv"
        file_vel = "vel.csv"
        
        self.logger.info("Saving the joints to CSV files")
        with open(file_pos, 'w') as csvfile:
            writer = csv.writer(csvfile)
            for array_str in joints.recorded_joints_pos:
                writer.writerow(array_str)
        
        with open(file_vel, 'w') as csvfile:
            writer = csv.writer(csvfile)
            for array_str in joints.recorded_joints_vel:
                writer.writerow(array_str)
    
    def _replay_from_csv(self):
        """
        Optional: Load CSV file to replay.
        In case you get the data from somewhere else (pybullet, ROS, etc).
        """
        file_pos = "pos.csv"
        file_vel = "vel.csv"
        
        recorded_joints_pos = []
        recorded_joints_vel = []
        
        with open(file_pos, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for line in csv_reader:
                recorded_joints_pos.append(line)
        
        with open(file_vel, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for line in csv_reader:
                recorded_joints_vel.append(line)
        
        self.logger.info("Replaying the joints from CSV files and go home")
        csv_joints = PandaJointsRecording(recorded_joints_pos, recorded_joints_vel)
        time.sleep(1)
        self.franka.motion_recorder.request(PlayRecordingRequest(csv_joints, self.frequency))
        self.franka.motion_recorder.request(GoHomeRequest())


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = FrankaMotionRecorderDemo()
    demo.run()




