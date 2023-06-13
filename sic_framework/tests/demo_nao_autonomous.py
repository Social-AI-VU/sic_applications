import time

from sic_framework.devices.common_naoqi.naoqi_autonomous import NaoqiAutonomous, \
    NaoWakeUpRequest, NaoBlinkingRequest, NaoSpeakingMovementRequest, NaoRestRequest,\
    NaoBasicAwarenessRequest, NaoListeningMovementRequest, NaoBackgroundMovingRequest

nao_autonomous = NaoqiAutonomous(ip="192.168.0.148")

print("Requesting NaoRestRequest")
reply = nao_autonomous.request(NaoRestRequest())
time.sleep(1)

print("Requesting wakeUp")
reply = nao_autonomous.request(NaoWakeUpRequest())
time.sleep(1)

print("Requesting Autonomous blinking on")
reply = nao_autonomous.request(NaoBlinkingRequest(True))
time.sleep(1)

print("Requesting NaoSpeakingMovementRequest")
reply = nao_autonomous.request(NaoSpeakingMovementRequest(True))
time.sleep(1)

print("Requesting NaoBasicAwarenessRequest")
reply = nao_autonomous.request(NaoBasicAwarenessRequest(True))
time.sleep(1)

print("Requesting NaoListeningMovementRequest")
reply = nao_autonomous.request(NaoListeningMovementRequest(True))
time.sleep(1)

print("Requesting NaoBackgroundMovingRequest")
reply = nao_autonomous.request(NaoBackgroundMovingRequest(True))
time.sleep(1)

# print("Requesting NaoRestRequest")
# reply = nao_autonomous.request(NaoRestRequest())
# time.sleep(1)
