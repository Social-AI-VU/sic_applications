# External imports
from operator import truediv
import os
import threading
import time
from collections import defaultdict

# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices import Pepper
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
    NaoRestRequest,
)
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_pepper.pepper_motion_streamer import (
    PepperMotionStreamerConf,
    StartStreaming,
    StopStreaming,
    SetLockedJointsRequest,
    GetLockedJointsRequest,
)
from sic_framework.devices.common_naoqi.naoqi_motion import (
    NaoqiMoveTowardRequest,
    NaoqiGetAnglesRequest,
    NaoqiSetAnglesRequest,
    NaoqiBreathingRequest,
    NaoqiSmartStiffnessRequest,
    NaoqiGetRobotVelocityRequest,
    NaoqiCollisionProtectionRequest,
    NaoqiMoveArmsEnabledRequest,
)


# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Set Redis password environment variable (when in developer mode)
os.environ['REDIS_PASSWORD'] = 'changemeplease'  # Do NOT actually change it
# Set Redis IP for robots to connect to your laptop (when in developer mode)
os.environ['DB_IP'] = 'localhost'  # Use local Redis server

# Robot IPs
PUPPET_IP = "XXX"
PERFORMER_IP = "XXX"

# Motion streaming configuration
ACTIVE_JOINTS = ["Head", "RArm", "LArm"]     # motion chains to stream
STREAM_HZ = 30                               # samples per second
VEL_THR = 0.02                               # m/s, below this we treat the robot as "still"
CHECK_DT = 0.2                               # seconds, how often to check velocity

# Blockage detection configuration
CRITICAL_JOINTS = {
    "LArm": ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll"],
    "RArm": ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"],
}

BLOCKAGE_CONFIG = {
    "angle_threshold": 0.25,                # radians - mismatch threshold
    "sustained_time": 1.0,                  # seconds - time to confirm blockage
    "blockage_ratio": 0.70,                 # fraction of recent samples that must show blockage
}


# ─────────────────────────────────────────────────────────────────────────────
# Puppeteering Application
# ─────────────────────────────────────────────────────────────────────────────
class PepperPuppeteeringDemo(SICApplication):
    """
    Pepper puppeteering demo application with joint locking and blockage detection.
    
    Demonstrates advanced control of two Pepper robots with pause/resume, joint locking,
    velocity-based collision protection, and blockage detection. Requires two Pepper robots.
    
    Robots
    ------
    - PUPPET: Pepper moved manually by the operator
    - PERFORMER: Pepper that mirrors the puppet's joint positions

    Controls
    --------
    - Back bumper: Pause/resume puppeteering
    - Right bumper: Lock/unlock right arm
    - Left bumper: Lock/unlock left arm  
    - Head sensor: Lock/unlock head
    - Press <Enter> (or Ctrl-C) in the terminal to finish the session

    Features
    --------
    Joint Locking:
        Uses chain-level stiffness calls for Pepper compatibility. SetLockedJointsRequest
        with chains ("LArm", "RArm", "Head"), NaoqiSetAnglesRequest for precise joint
        positioning, motion streamer continuously maintains locked positions, and
        walking-engine arm swing disabled to prevent interference with locking.

    Velocity-Based Collision Protection:
        Dynamically manages collision protection based on robot movement. Disables
        protection when stationary (velocity < 0.02 m/s), re-enables protection when
        moving, and allows human interaction without breaking motion streamer.

    Blockage Detection:
        Monitors joint angle mismatches between puppet and performer using 5 Hz sampling
        of critical joints (shoulders, elbows). Provides visual feedback via chest LED
        (red = blockage detected) with configurable thresholds for sensitivity.

    Pause/Resume:
        Comprehensive pause system with state preservation. Stops motion streaming and
        sets velocity to zero, pauses blockage detection to prevent false alarms, and
        maintains locking states for seamless resumption.

    Both robots are always returned to a safe rest pose when the program exits.
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(PepperPuppeteeringDemo, self).__init__()
        
        # Demo-specific configuration
        self.puppet_ip = PUPPET_IP
        self.performer_ip = PERFORMER_IP
        self.active_joints = ACTIVE_JOINTS
        self.stream_hz = STREAM_HZ
        
        # Robot instances
        self.puppet = None
        self.performer = None
        self.puppet_motion = None
        self.performer_motion = None
        
        # Threading locks
        self._blockage_lock = threading.Lock()
        self._angle_lock = threading.Lock()

        # State variables
        self._paused = False                        # True if the puppeteering is paused
        self._prot_off = False                      # True if collision protection is off
        self._vel_mon_stop = threading.Event()      # Event to stop velocity monitoring
        self._vel_mon_thr = None                    # Thread to monitor velocity
        self._blockage_paused = threading.Event()   # Event to pause blockage detection
        self._blockage_stop = threading.Event()     # Event to stop blockage detection
        
        # Joint locking state
        self._locked_joints = set()                 # Set of locked joint chains
        self._locked_angles = {}                    # Angles to maintain for locked joints

        # Blockage detection state
        self._puppet_angles = {}                    # Latest puppet joint angles
        self._performer_angles = {}                 # Latest performer joint angles
        self._hist = defaultdict(list)              # per-chain time-series
        self._active_blockages = set()              # chains currently blocked
        
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/pepper/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure both Pepper robots."""
        self.logger.info("Starting Pepper Puppeteering Demo (Complex)...")
        
        # Motion-streamer configurations
        puppet_conf = PepperMotionStreamerConf(samples_per_second=self.stream_hz, stiffness=0.0)
        performer_conf = PepperMotionStreamerConf(samples_per_second=self.stream_hz, stiffness=1.0)

        self.puppet = Pepper(self.puppet_ip, pepper_motion_conf=puppet_conf)
        self.performer = Pepper(self.performer_ip, pepper_motion_conf=performer_conf)

        # Initialize robots
        self._initialise_robots()

        # Start background threads
        self._blockage_thr = threading.Thread(target=self._blockage_watchdog, daemon=True)
        self._blockage_thr.start()

        # Register sensor callbacks
        self._register_sensor_callbacks()

        # Start velocity monitoring
        self._start_velocity_monitor()
        
        self.logger.info("Both robots initialized successfully")


    # ---------------------------------------------------------------------
    # Initialisation
    # ---------------------------------------------------------------------
    def _initialise_robots(self):
        """Initialize both robots for puppeteering.
        
        This method sets up both robots for safe puppeteering operation by:
        1. Disabling autonomous behaviors that could interfere with manual control
        2. Waking up the robots (required for stiffness control)
        3. Disabling smart stiffness and breathing animations
        4. Disabling arm swing so arms stay locked during movement
        5. Setting appropriate initial stiffness values
        6. Connecting the motion streaming between robots
        """
        # Disable autonomous behaviour that interferes with manual control
        self.puppet.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        self.performer.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))

        # Wake up (Pepper cannot change stiffness while in rest)
        self.puppet.autonomous.request(NaoWakeUpRequest())
        self.performer.autonomous.request(NaoWakeUpRequest())

        # Disable smart stiffness and breathing for proper teleoperation
        self.puppet.motion.request(NaoqiSmartStiffnessRequest(False))
        self.performer.motion.request(NaoqiSmartStiffnessRequest(False))
        self.puppet.motion.request(NaoqiBreathingRequest("Arms", False))
        self.performer.motion.request(NaoqiBreathingRequest("Arms", False))

        # Stop NAOqi's walking controller from grabbing the arms
        try:
            for r in (self.puppet, self.performer):
                r.motion.request(NaoqiMoveArmsEnabledRequest(False, False))
            self.logger.info("✓ Walking-engine arm swing disabled on both robots")
        except Exception as e:
            self.logger.warning("Warning: Could not disable arm swing: {}".format(e))
            self.logger.warning("Continuing without arm swing disable...")

        # Puppet: zero stiffness on streamed chains so the operator can move joints
        self.puppet.stiffness.request(
            Stiffness(0, joints=ACTIVE_JOINTS, enable_joint_list_generation=False)
        )
        self.performer_stiffness = self.performer.stiffness
        
        # Connect performer's motion-stream input to the master's output
        self.puppet_motion = self.puppet.motion_streaming()
        self.performer_motion = self.performer.motion_streaming(input_source=self.puppet_motion)

        self._register_stream_callback()

    def _register_sensor_callbacks(self):
        """Register callbacks for all sensor inputs.
        
        This method sets up event handlers for all the robot's sensors:
        - Back bumper: Pause/resume puppeteering
        - Right bumper: Lock/unlock right arm
        - Left bumper: Lock/unlock left arm
        - Head sensor: Lock/unlock head
        
        Each callback is registered with error handling to ensure robust operation.
        """
        sensors = [
            (self.puppet.back_bumper, self._on_back_bumper, "Back bumper"),
            (self.puppet.right_bumper, self._on_right_bumper, "Right bumper"),
            (self.puppet.left_bumper, self._on_left_bumper, "Left bumper"),
            (self.puppet.tactile_sensor, self._on_head_touch, "Head sensor"),
        ]
        
        for sensor, callback, name in sensors:
            try:
                sensor.register_callback(callback)
                self.logger.info("✓ {} callback registered successfully".format(name))
            except Exception as e:
                self.logger.error("✗ Error registering {} callback: {}".format(name, e))

    # ---------------------------------------------------------------------
    # Convenience wrappers
    # ---------------------------------------------------------------------
    def _say(self, text: str) -> None:
        """
        Make the puppet speak the given text.
        """
        self.puppet.tts.request(
            NaoqiTextToSpeechRequest(text, language="English")
        )

    def _start_streaming(self) -> None:        
        """
        Start motion streaming between robots.
        """
        self.puppet_motion.request(StartStreaming(ACTIVE_JOINTS))

    def _stop_streaming(self) -> None:
        """
        Stop motion streaming between robots.
        """
        self.puppet_motion.request(StopStreaming())
    
    def _pause_puppeteering(self) -> None:
        """
        Pause all puppeteering (joints and base).
        
        This method provides a comprehensive pause functionality that:
        1. Stops motion streaming between robots
        2. Sets the performer's velocity to zero to stop base movement
        3. Pauses blockage detection to prevent false alarms during manual intervention
        4. Clears blockage state since we're pausing
        """
        self._stop_streaming()
        self._say("Pausing puppeteering.")
        # Set velocity to 0 to stop base movement
        self.performer.motion.request(NaoqiMoveTowardRequest(0.0, 0.0, 0.0))
        # Pause blockage detection to avoid false alarms
        self._blockage_paused.set()
        # Clear blockage state since we're pausing
        self._clear_blockage_state()
    
    def _resume_puppeteering(self) -> None:
        """
        Resume all puppeteering (joints and base).
        
        This method restarts the puppeteering system after a pause by:
        1. Restarting motion streaming between robots
        2. Resuming blockage detection
        
        The system resumes with the current robot states and locking configurations.
        """
        self._start_streaming()
        self._say("Resuming puppeteering.")
        # Resume blockage detection
        self._blockage_paused.clear()
    
    def _lock_joint(self, chain: str):
        """Lock a joint chain in its current position using chain-level stiffness calls.
        
        This method implements the joint locking mechanism using Pepper's chain-level
        stiffness API. The process involves:
        
        1. Capturing current angles from the puppet for the specified chain
        2. Telling the motion streamer to maintain stiffness=1.0 for these chains
        3. Setting the captured angles on both robots to lock them in position
        4. The motion streamer will continuously send these frozen angles to maintain position
        
        Args:
            chain: The joint chain to lock ("LArm", "RArm", or "Head")
            
        Note:
            This method uses chain-level stiffness calls ("LArm", "RArm", "Head") that
            Pepper actually responds to, unlike individual joint stiffness calls.
            Individual joint angles are still used for precise positioning.
        """
        self.logger.info(f"Attempting to lock {chain}...")
        if chain in self._locked_joints:
            self.logger.info(f"{chain} is already locked")
            return
            
        try:
            self._locked_joints.add(chain)
            self.logger.info(f"Added {chain} to locked joints set: {self._locked_joints}")

            # Use chain-level stiffness calls for Pepper (not individual joints)
            phys = [chain]  # "LArm", "RArm", or "Head"

            # Remember current puppet angles (still get individual joint angles for position)
            individual_joints = ["HeadYaw", "HeadPitch"] if chain == "Head" else CRITICAL_JOINTS[chain]
            self.logger.info(f"Getting angles for joints: {individual_joints}")
            angles_response = self.puppet.motion.request(NaoqiGetAnglesRequest(individual_joints, True))
            angles = angles_response.angles
            self._locked_angles.update(dict(zip(individual_joints, angles)))
            self.logger.info(f"Stored locked angles: {self._locked_angles}")

            # Tell both robots to lock these chains (motion streamer will set stiffness=1.0)
            self.logger.info(f"Sending locked joints to motion streamers: {list(self._locked_joints)}")

            self.logger.info(f"Sending to robot {self.puppet.device_ip}...")
            self.puppet_motion.request(SetLockedJointsRequest(list(self._locked_joints)))
            self.logger.info(f"Sent to robot {self.puppet.device_ip}")

            self.logger.info(f"Sending to robot {self.performer.device_ip}...")
            self.performer_motion.request(SetLockedJointsRequest(list(self._locked_joints)))
            self.logger.info(f"Sent to robot {self.performer.device_ip}")

            # Set the captured angles on both robots to lock them in position
            angle_values = [self._locked_angles[joint] for joint in individual_joints]
            self.logger.info(f"Setting angles on both robots: {dict(zip(individual_joints, angle_values))}")
            for robot in (self.puppet, self.performer):
                robot.motion.request(
                    NaoqiSetAnglesRequest(individual_joints, angle_values, speed=0.5)
                )
            
            self.logger.info(f"✓ {chain} locked successfully")
            
        except Exception as e:
            self.logger.error("✗ Error locking {}: {}".format(chain, e))
            # Rollback on error
            self._locked_joints.discard(chain)
            for joint in individual_joints:
                self._locked_angles.pop(joint, None)

    
    def _unlock_joint(self, chain: str):
        """Unlock a joint chain to allow normal puppeteering.
        
        This method removes the locking constraint from a previously locked joint chain.
        The process involves:
        
        1. Removing the chain from the locked joints set
        2. Telling the motion streamer to stop maintaining stiffness=1.0 for these chains
        3. Setting appropriate stiffness for the unlocked chain
        4. Clearing the stored angles for this chain
        
        Args:
            chain: The joint chain to unlock ("LArm", "RArm", or "Head")
            
        Note:
            The chain remains in streaming (was never removed) so normal puppeteering
            resumes immediately after unlocking.
        """
        self.logger.info(f"Attempting to unlock {chain}...")
        if chain not in self._locked_joints:
            self.logger.info(f"{chain} is not locked")
            return
            
        try:
            self._locked_joints.remove(chain)

            # Use chain-level stiffness calls for Pepper (not individual joints)
            phys = [chain]  # "LArm", "RArm", or "Head"

            # Tell both robots that the chain is no longer locked
            self.puppet_motion.request(SetLockedJointsRequest(list(self._locked_joints)))
            self.performer_motion.request(SetLockedJointsRequest(list(self._locked_joints)))

            # Reset stiffness for unlocked chains - puppet gets 0.0, performer gets 1.0
            self.puppet.stiffness.request(Stiffness(0.0, joints=phys, enable_joint_list_generation=False))
            self.performer.stiffness.request(Stiffness(1.0, joints=phys, enable_joint_list_generation=False))

            # Clear stored angles for this chain
            individual_joints = ["HeadYaw", "HeadPitch"] if chain == "Head" else CRITICAL_JOINTS[chain]
            for joint in individual_joints:
                self._locked_angles.pop(joint, None)
                
            self.logger.info("✓ {} unlocked".format(chain))
            
        except Exception as e:
            self.logger.error("✗ Error unlocking {}: {}".format(chain, e))
            # Rollback on error - add back to locked joints
            self._locked_joints.add(chain)
    
    # ---------------------------------------------------------------------
    # Chest LED update
    # ---------------------------------------------------------------------
    def _update_chest_led(self):
        """Update chest LED color based on blockage state.
        
        This method provides visual feedback by changing the puppet's chest LED color:
        - Red light: Indicates active blockage detected on any arm
        - Off: No blockage detected
        
        The LED provides immediate visual feedback to the operator about the system state.
        """
        if any(chain in self._active_blockages for chain in CRITICAL_JOINTS.keys()):
            color = (1.0, 0.0, 0.0)  # red light to indicate blockage
        else:
            color = (0.0, 0.0, 0.0)  # lights off when blockage no longer detected
        try:
            self.puppet.leds.request(NaoFadeRGBRequest("ChestLeds", *color))
        except Exception as e:
            self.logger.error("LED error:", e)
    
    # -------------------------------------------------------------------------
    # Motion-stream callback: keeps _puppet_angles current
    # -------------------------------------------------------------------------
    def _register_stream_callback(self):
        """Register callback for motion streaming.
        
        This method sets up the callback that processes incoming motion stream packets
        from the puppet robot, keeping the internal angle state current and handling
        locked joint angle overrides.
        """
        self.puppet_motion.register_callback(self._on_stream_packet)

    def _on_stream_packet(self, msg):
        """Handle incoming motion stream packets.
        
        This callback processes motion stream packets from the puppet robot and:
        1. Updates the internal puppet angle state for blockage detection
        
        Args:
            msg: The PepperMotionStream message containing joint angles and velocity
        """
        try:
            with self._angle_lock:
                # Update puppet angles for blockage detection
                self._puppet_angles.update(dict(zip(msg.joints, msg.angles)))
                                
        except Exception as e:
            self.logger.error("Stream-callback error:", e)

    # ---------------------------------------------------------------------
    # Sensor callbacks
    # ---------------------------------------------------------------------
    def _on_back_bumper(self, msg) -> None:
        """Handle back bumper press - toggle pause/resume.
        
        This callback implements the pause/resume functionality using the back bumper.
        When pressed, it toggles between paused and resumed states, providing
        immediate control over the puppeteering system for safety and convenience.
        
        Args:
            msg: The bumper sensor message containing the press state
        """
        self.logger.info(f"Back bumper pressed: value={msg.value}, paused={self._paused}")
        if msg.value != 1:      # ignore release
            return

        if self._paused:        # → RESUME
            try:
                self._resume_puppeteering()
            except Exception as e:
                self.logger.error("Error resuming puppeteering:", e)
            else:
                # self._say("Resuming puppeteering.")
                self._paused = False
        else:                   # → PAUSE
            try:
                self._pause_puppeteering()
            except Exception as e:
                self.logger.error("Error pausing puppeteering:", e)
            else:
                # self._say("Pausing puppeteering.")
                self._paused = True
    
    def _on_right_bumper(self, msg) -> None:
        """
        Handle right bumper press - toggle right arm lock.
        
        Args:
            msg: The bumper sensor message containing the press state
        """
        self.logger.info(f"Right bumper pressed: value={msg.value}")
        if msg.value != 1:      # ignore release
            return
        
        if "RArm" in self._locked_joints:  # → UNLOCK
            self._say("Unlocking right arm... please wait...")
            self._unlock_joint("RArm")
            self._say("Right arm unlocked.")
        else:                              # → LOCK
            self._say("Locking right arm... please wait...")
            self._lock_joint("RArm")
            self._say("Right arm locked.")
    
    def _on_left_bumper(self, msg) -> None:
        """
        Handle left bumper press - toggle left arm lock.
        
        Args:
            msg: The bumper sensor message containing the press state
        """
        self.logger.info(f"Left bumper pressed: value={msg.value}")
        if msg.value != 1:      # ignore release
            return
        
        if "LArm" in self._locked_joints:  # → UNLOCK
            self._say("Unlocking left arm... please wait...")
            self._unlock_joint("LArm")
            self._say("Left arm unlocked. You can now move it freely.")
        else:                              # → LOCK
            self._say("Locking left arm... please wait...")
            self._lock_joint("LArm")
            self._say("Left arm locked.")
    
    def _on_head_touch(self, msg) -> None:
        """
        Handle head sensor touch - toggle head lock.
        
        Args:
            msg: The tactile sensor message containing the touch state
        """
        self.logger.info(f"Head sensor touched: value={msg.value}")
        if msg.value != 1:      # ignore release
            return
        
        if "Head" in self._locked_joints:  # → UNLOCK
            self._say("Unlocking head... please wait...")
            self._unlock_joint("Head")
            self._say("Head unlocked. You can now move it freely.")
        else:                              # → LOCK
            self._say("Locking head... please wait...")
            self._lock_joint("Head")
            self._say("Head locked.")
    
    # ---------------------------------------------------------------------
    # Blockage detection
    # ---------------------------------------------------------------------
    def _analyse_blockages(self, now):
        """Analyze joint blockages and update state.
        
        This method implements the blockage detection algorithm that monitors
        the difference between commanded and actual joint angles. The algorithm:
        
        1. Compares puppet commanded angles with performer sensed angles
        2. Calculates the maximum absolute error for each arm chain
        3. Maintains a time-series history of blockage states
        4. Applies threshold-based detection with sustained time requirements
        5. Updates visual feedback (chest LED) when blockage state changes
        
        Currently provides visual (chest LED) and auditory (voice) feedback only.
        Haptic feedback (increasing puppet joint stiffness based on angle mismatch)
        could not be implemented due to the motion streamer constantly resetting
        stiffness to 0.0 for streamed joints. You can manage the sensitivity of the
        blockage detection by modifying the values in BLOCKAGE_CONFIG.
        
        Args:
            now: Current timestamp for the analysis
        """
        with self._angle_lock:
            puppet_snapshot = self._puppet_angles.copy()
            performer_snapshot = self._performer_angles.copy()
        
        H = self._hist
        prev_blockages = set(self._active_blockages)  # Save previous state

        for chain, joints in CRITICAL_JOINTS.items():
            # max absolute error among that chain's joints
            err = max(
                abs(puppet_snapshot.get(j, 0) - performer_snapshot.get(j, 0))
                for j in joints
            )

            blocked = err > BLOCKAGE_CONFIG["angle_threshold"]
            H[chain].append((now, blocked))

            # forget stale samples
            cutoff = now - BLOCKAGE_CONFIG["sustained_time"]
            H[chain] = [(t, b) for (t, b) in H[chain] if t >= cutoff]

            # decide persistent blockage
            if H[chain]:
                ratio = sum(b for _, b in H[chain]) / float(len(H[chain]))
                pers = ratio >= BLOCKAGE_CONFIG["blockage_ratio"]
                if pers and chain not in self._active_blockages:
                    self._active_blockages.add(chain)
                    self._say(f"{chain} mismatch")
                    self.logger.info(f"*** {chain} BLOCKAGE DETECTED ***")
                elif not pers and chain in self._active_blockages:
                    self._active_blockages.remove(chain)
                    self.logger.info(f"*** {chain} BLOCKAGE CLEARED ***")

        # If the set of blockages changed, update the chest LED
        if self._active_blockages != prev_blockages:
            self._update_chest_led()

    # ---------------------------------------------------------------------
    # Velocity monitoring
    # ---------------------------------------------------------------------
    def _start_velocity_monitor(self):
        """
        Start velocity monitoring thread.
        """
        if self._vel_mon_thr and self._vel_mon_thr.is_alive():
            return
        self._vel_mon_stop.clear()
        self._vel_mon_thr = threading.Thread(
            target=self._velocity_loop, daemon=True
        )
        self._vel_mon_thr.start()

    def _stop_velocity_monitor(self):
        """
        Stop velocity monitoring thread.
        """
        self._vel_mon_stop.set()
        if self._vel_mon_thr:
            self._vel_mon_thr.join()

    def _velocity_loop(self):
        """Monitor robot velocity and manage collision protection.
        
        This method runs in a separate thread and continuously monitors the
        performer robot's velocity to implement intelligent collision protection:
        
        1. Samples velocity at regular intervals (CHECK_DT)
        2. When velocity is below threshold (VEL_THR), disables collision protection
           for arms to allow human interaction without breaking the motion streamer
        3. When movement is detected, re-enables collision protection for safety
        4. Provides dynamic safety management based on robot activity
        
        This approach balances safety with usability by allowing interaction
        when the robot is stationary while maintaining protection during movement.
        """
        while not self._vel_mon_stop.is_set():
            try:
                velocity_response = self.performer.motion.request(
                    NaoqiGetRobotVelocityRequest()
                )
                # Handle the response properly
                if hasattr(velocity_response, 'x'):
                    vx, vy, vth = velocity_response.x, velocity_response.y, velocity_response.theta
                else:
                    vx, vy, vth = velocity_response[0], velocity_response[1], velocity_response[2]
                
                # Dynamic collision protection management
                v_mag = (vx**2 + vy**2 + vth**2)**0.5
                
                if v_mag < VEL_THR and not self._prot_off:
                    # Robot is stationary - disable collision protection for arms
                    self.puppet.motion.request(NaoqiCollisionProtectionRequest("Arms", False))
                    self.performer.motion.request(NaoqiCollisionProtectionRequest("Arms", False))
                    self._prot_off = True
                    self.logger.info(f"Velocity: ({vx:.3f}, {vy:.3f}, {vth:.3f}) - Collision protection disabled")
                elif v_mag >= VEL_THR and self._prot_off:
                    # Robot is moving - re-enable collision protection
                    self.puppet.motion.request(NaoqiCollisionProtectionRequest("Arms", True))
                    self.performer.motion.request(NaoqiCollisionProtectionRequest("Arms", True))
                    self._prot_off = False
                    self.logger.info(f"Velocity: ({vx:.3f}, {vy:.3f}, {vth:.3f}) - Collision protection enabled")
                
            except Exception as e:
                self.logger.error(f"Velocity monitor error: {e}")
            time.sleep(CHECK_DT)

    # -------------------------------------------------------------------------
    # Blockage watchdog – runs at ~5 Hz, independent of streaming rate
    # -------------------------------------------------------------------------
    def _blockage_watchdog(self):
        """Monitor for joint blockages at 5 Hz.
        
        This method runs in a separate thread and continuously monitors for
        joint blockages by comparing puppet commanded angles with performer
        sensed angles. It operates independently of the motion streaming rate
        to provide consistent blockage detection.
        
        The method:
        1. Samples performer joint angles at regular intervals
        2. Compares them with puppet commanded angles
        3. Calls the blockage analysis function
        4. Maintains proper timing for consistent detection
        """
        SAMPLE_PERIOD = 0.20                      # 5 Hz
        names = [j for chain in ("LArm", "RArm") for j in CRITICAL_JOINTS[chain]]
        while not self._blockage_stop.is_set():
            # Check if blockage detection is paused
            if self._blockage_paused.is_set():
                time.sleep(SAMPLE_PERIOD)
                continue
                
            t0 = time.time()

            # -------- gather angles from performer -------------
            try:
                with self._blockage_lock:
                    response = self.performer.motion.request(NaoqiGetAnglesRequest(names, True))
                    sensed = response.angles
                with self._angle_lock:
                    self._performer_angles = dict(zip(names, sensed))
            except Exception as e:
                self.logger.error(f"Error getting performer angles: {e}")
                # robot may be booting – just skip this cycle
                time.sleep(SAMPLE_PERIOD)
                continue

            # -------- compare with puppet commanded angles ----
            self._analyse_blockages(time.time())

            # pacing
            dt = time.time() - t0
            if dt < SAMPLE_PERIOD:
                time.sleep(SAMPLE_PERIOD - dt)

    # ---------------------------------------------------------------------
    # Public entry point
    # ---------------------------------------------------------------------
    def run(self) -> None:
        """Main application logic.
        
        This method starts the puppeteering session and handles the main event loop.
        It initializes the system, starts motion streaming, and waits for user
        input to terminate the session. The method ensures proper cleanup
        regardless of how the session ends.
        """
        try:
            self.logger.info("Starting puppeteering session. Press <Enter> to stop.")
            
            # Start puppeteering
            self._say("Start puppeteering.")
            self._start_streaming()
            
            # Wait for user input
            input()
            
            self.logger.info("Stopping puppeteering session...")
            
        except KeyboardInterrupt:
            self.logger.info("Interrupt received. Stopping session.")
        except Exception as e:
            self.logger.error("Error in puppeteering demo: {}".format(e))
        finally:
            self.shutdown()

    # ---------------------------------------------------------------------
    # Clean-up
    # ---------------------------------------------------------------------
    def _clear_blockage_state(self):
        """Clear all blockage and locking state.
        
        This method resets all blockage detection and joint locking state,
        clearing the history, active blockages, and locked joints. It also
        updates the visual feedback to reflect the cleared state.
        """
        self._hist.clear()
        self._active_blockages.clear()
        self._update_chest_led()
        
        # Clear locked joints when pausing
        self._locked_joints.clear()
        self._locked_angles.clear()

    def shutdown(self) -> None:
        """Clean shutdown of the puppeteering session.
        
        This method performs a comprehensive cleanup of the puppeteering session:
        1. Clears all state (blockages, locks)
        2. Stops motion streaming
        3. Stops velocity monitoring
        4. Stops blockage detection
        5. Restores robot stiffness
        6. Re-enables autonomous life
        7. Puts robots into rest pose
        
        This ensures both robots are left in a safe, stable state.
        """
        self.logger.info("Shutting down puppeteering demo...")
        
        # Announce shutdown
        self._say("We are done puppeteering.")
        self._clear_blockage_state()
        self._stop_streaming()
        
        try:
            # guarantee a hard stop
            self.performer.motion.request(
                NaoqiMoveTowardRequest(0.0, 0.0, 0.0)
            )
        except Exception as e:
            self.logger.warning("Error stopping performer movement: {}".format(e))

        # Stop velocity monitoring
        self.logger.info("Stopping velocity monitoring...")
        self._stop_velocity_monitor()

        # Stop blockage detection
        self.logger.info("Stopping blockage detection...")
        self._blockage_stop.set()
        if hasattr(self, '_blockage_thr') and self._blockage_thr:
            self._blockage_thr.join(timeout=2.0)  # Wait up to 2 seconds for clean shutdown

        # Reset stiffness for all chains before rest
        # This ensures both robots are in a proper state for rest
        self.logger.info("Resetting stiffness for all chains...")
        for chain in self.active_joints:
            try:
                self.puppet.stiffness.request(Stiffness(0.7, joints=[chain], enable_joint_list_generation=False))
                self.performer.stiffness.request(Stiffness(0.7, joints=[chain], enable_joint_list_generation=False))
            except Exception as e:
                self.logger.warning("Error resetting stiffness for {}: {}".format(chain, e))

        # Restore puppet stiffness before rest (backup method)
        self.puppet.stiffness.request(
            Stiffness(0.7, joints=self.active_joints, enable_joint_list_generation=False)
        )

        # Re-enable autonomous life (optional but recommended for Pepper)
        self.logger.info("Re-enabling autonomous life...")
        self.puppet.autonomous.request(NaoSetAutonomousLifeRequest("solitary"))
        self.performer.autonomous.request(NaoSetAutonomousLifeRequest("solitary"))

        # Put both robots into rest
        self.logger.info("Putting robots into rest pose...")
        self.puppet.autonomous.request(NaoRestRequest())
        self.performer.autonomous.request(NaoRestRequest())

        self.logger.info("Session ended; both Peppers are in rest pose.")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Create and run the demo
    demo = PepperPuppeteeringDemo()
    demo.run()