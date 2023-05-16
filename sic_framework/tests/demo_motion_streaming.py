import time

from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoMotionStreamer, StartStreaming, StopStreaming

a = NaoMotionStreamer("192.168.0.180")


b = NaoMotionStreamer("192.168.0.151")


a.connect(b)

b.request(StartStreaming(["Head"]))

time.sleep(10)

a.request(StopStreaming())
