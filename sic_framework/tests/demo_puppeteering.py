import time

from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoqiMotionStreamer, StartStreaming, StopStreaming, \
    NaoMotionStreamerConf

conf = NaoMotionStreamerConf(samples_per_second=60)

streamer = NaoqiMotionStreamer("192.168.0.151", conf=conf)


consumer = NaoqiMotionStreamer("192.168.0.210")
consumer.connect(streamer)

streamer.request(StartStreaming(["Torso"]))

time.sleep(10)
print("Done")
streamer.request(StopStreaming())
