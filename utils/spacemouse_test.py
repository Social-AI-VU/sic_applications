import pyspacemouse

# Context manager (recommended) - automatically closes device
with pyspacemouse.open() as device:
    while True:
        state = device.read()
        print(state.x, state.y, state.z)