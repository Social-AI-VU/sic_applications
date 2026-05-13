"""
Reads and prints the translation axes (x, y, z) of a connected SpaceMouse device in real time.

This script uses the pyspacemouse library to connect to a SpaceMouse. It repeatedly reads the
current state from the device and prints the x, y, z translation values every 0.1 seconds.
Automatically closes the device when finished.
"""

import pyspacemouse
import time

# Context manager (recommended) - automatically closes device
with pyspacemouse.open() as device:
    while True:
        state = device.read()
        print(state.x, state.y, state.z)
        time.sleep(0.1)