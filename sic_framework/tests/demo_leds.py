import time

from sic_framework.devices import Pepper
from sic_framework.devices.common_naoqi.naoqi_leds import NaoLEDRequest, \
    NaoFadeRGBRequest

pepper = Pepper(ip="192.168.0.148")

print("Requesting Eye LEDs to turn on")
reply = pepper.leds.request(NaoLEDRequest("Eyes", True))


print("Setting Eye LEDs to red")
reply = pepper.leds.request(NaoFadeRGBRequest("FaceLedRight0", 0, 0, 0, 0))

time.sleep(1)

reply = pepper.leds.request(NaoFadeRGBRequest("FaceLedRight0", 1, 0, 0, 0))



