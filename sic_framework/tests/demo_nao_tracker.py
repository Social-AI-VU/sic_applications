import time
from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_tracker import RegisterTargetRequest, StartTrackRequest, StopTrackRequest

# Connect to NAO
nao = Nao(ip="192.168.0.0")

# Add target to track.
target_name = "Face"
nao.tracker.request(RegisterTargetRequest(target_name, 0.3))

# Start tracking
nao.tracker.request(StartTrackRequest(target_name))

# Do some stuff here
time.sleep(10)

# Stop tracking
nao.tracker.request(StopTrackRequest())
