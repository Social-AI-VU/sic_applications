import time

from sic_framework.devices.minirobot import MiniRobot
from sic_framework.devices.common_mini.mini_animation import MiniActionRequest

"""
This demo shows how to make Nao perform predefined postures and animations.
"""

mini = MiniRobot()
mini.animation.request(MiniActionRequest("018"))
