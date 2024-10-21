import time

from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_leds import NaoLEDRequest, NaoFadeRGBRequest

nao = Nao(ip="192.168.2.7")

print("Requesting Eye LEDs to turn on")
reply = nao.leds.request(NaoLEDRequest("FaceLeds", True))
time.sleep(1)

print("Setting right Eye LEDs to red")
reply = nao.leds.request(NaoFadeRGBRequest("RightFaceLeds", 1, 0, 0, 0))

time.sleep(1)

print("Setting left Eye LEDs to blue")
reply = nao.leds.request(NaoFadeRGBRequest("LeftFaceLeds", 0, 0, 1, 0))
