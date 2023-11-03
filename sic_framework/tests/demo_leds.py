import time

from sic_framework.devices import Pepper
from sic_framework.devices.common_naoqi.naoqi_leds import NaoLEDRequest, NaoFadeRGBRequest

pepper = Pepper(ip="192.168.0.148")

print("Requesting Eye LEDs to turn on")
reply = pepper.leds.request(NaoLEDRequest("FaceLeds", True))
time.sleep(1)

print("Setting right Eye LEDs to red")
reply = pepper.leds.request(NaoFadeRGBRequest("RightFaceLeds", 1, 0, 0, 0))

time.sleep(1)

print("Setting left Eye LEDs to blue")
reply = pepper.leds.request(NaoFadeRGBRequest("LeftFaceLeds", 0, 0, 1, 0))
