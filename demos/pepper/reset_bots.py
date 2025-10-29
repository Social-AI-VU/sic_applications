#!/usr/bin/env python3
"""
Robot Manual Drive Script
------------------------
Script to put robots in manual drive mode for relocation.

Usage:
    python reset_bots.py

This script will:
1. Connect to both robots
2. Put them in a state where they can be manually driven
3. Disable all autonomous behaviors and collision protection
4. Allow manual movement without resistance

Use this to relocate robots between tasks.
"""

# External imports
import os

# SIC imports
from sic_framework.devices import Pepper
from sic_framework.devices.common_naoqi.naoqi_stiffness import Stiffness
from sic_framework.devices.common_naoqi.naoqi_leds import NaoFadeRGBRequest
from sic_framework.devices.common_naoqi.naoqi_autonomous import (
    NaoSetAutonomousLifeRequest,
    NaoWakeUpRequest,
    NaoRestRequest,
)
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest
from sic_framework.devices.common_naoqi.pepper_motion_streamer import (
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
# Set Redis password environment variable
os.environ['REDIS_PASSWORD'] = 'changemeplease'

# Developer mode flag
# Only use developer mode if you made changes to the social-interaction-cloud that need
# to be installed on the robots.
DEV_MODE = True

# Robot IPs
PUPPET_IP = "10.0.0.168"
PERFORMER_IP = "10.0.0.196"

# ─────────────────────────────────────────────────────────────────────────────
# Manual Drive Function
# ─────────────────────────────────────────────────────────────────────────────
def enable_manual_drive():
    """Put robots in manual drive mode for relocation."""
    
    print("Connecting to robots...")
    
    # Connect to robots
    if DEV_MODE:
        # Use dev_test mode with repo path to install new code on the robots
        puppet = Pepper(PUPPET_IP, dev_test=True)
        performer = Pepper(PERFORMER_IP, dev_test=True)
    else:
        # Use standard connection
        puppet = Pepper(PUPPET_IP)
        performer = Pepper(PERFORMER_IP)
    
    try:
        print("Setting up robots for manual drive...")
        
        # Wake up robots (required for control)
        puppet.autonomous.request(NaoWakeUpRequest())
        performer.autonomous.request(NaoWakeUpRequest())
        
        # Disable all autonomous behaviors
        puppet.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        performer.autonomous.request(NaoSetAutonomousLifeRequest("disabled"))
        
        # Disable smart stiffness and breathing
        puppet.motion.request(NaoqiSmartStiffnessRequest(False))
        performer.motion.request(NaoqiSmartStiffnessRequest(False))
        puppet.motion.request(NaoqiBreathingRequest("Arms", False))
        performer.motion.request(NaoqiBreathingRequest("Arms", False))
        
        # Set velocity to zero to stop any movement
        puppet.motion.request(NaoqiMoveTowardRequest(0.0, 0.0, 0.0))
        performer.motion.request(NaoqiMoveTowardRequest(0.0, 0.0, 0.0))
        
        print("✓ Robots are ready for manual drive!")
        print("  - Both robots are awake but autonomous behaviors disabled")
        print("  - Smart stiffness and breathing disabled")
        print("  - Movement stopped")
        print("  - You can now manually drive them around")
        print()
        print("When you're done relocating the robots, press Enter to put them to rest...")
        
        # Wait for user to finish moving robots
        input()
        
        print("Putting robots to rest...")
        
        # Put robots to rest
        puppet.autonomous.request(NaoRestRequest())
        performer.autonomous.request(NaoRestRequest())
        
        print("✓ Both robots are now in rest mode")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Attempting to put robots to rest anyway...")
        
        try:
            puppet.autonomous.request(NaoRestRequest())
            performer.autonomous.request(NaoRestRequest())
            print("✓ Robots put to rest successfully")
        except:
            print("✗ Failed to put robots to rest")
    
    finally:
        print("\nManual drive complete. You can now start your next task.")


# ─────────────────────────────────────────────────────────────────────────────
# Script entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Robot Manual Drive Script")
    print("=========================")
    print("This script will put robots in manual drive mode for relocation.")
    print("You can then manually drive them to new positions.")
    print()
    
    input("Press Enter to enable manual drive mode...")
    
    enable_manual_drive() 