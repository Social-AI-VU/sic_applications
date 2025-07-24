
"""
This demo shows how to make Nao perform predefined postures and animations.
"""

import time

from sic_framework.devices.alphamini import Alphamini
from sic_framework.devices.common_mini.mini_animation import MiniActionRequest

mini = Alphamini()
mini.animation.request(MiniActionRequest("018"))
