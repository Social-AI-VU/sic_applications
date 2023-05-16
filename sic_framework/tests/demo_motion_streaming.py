import time

from sic_framework.devices.common_naoqi.naoqi_motion_streamer import NaoMotionStreamer, StartStreaming, StopStreaming, \
    NaoMotionStreamerConf

conf = NaoMotionStreamerConf(samples_per_second=60)

streamer = NaoMotionStreamer("192.168.0.151", conf=conf)


consumer = NaoMotionStreamer("192.168.0.210")
consumer.connect(streamer)

streamer.request(StartStreaming(["Head"]))

time.sleep(10)
print("Done")
streamer.request(StopStreaming())
