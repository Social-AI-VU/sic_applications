from sic_framework.devices import Nao
from sic_framework.devices.common_naoqi.naoqi_text_to_speech import NaoqiTextToSpeechRequest

nao = Nao(ip='192.168.0.151')

# waits for the robot to finish talking
nao.tts.request(NaoqiTextToSpeechRequest("Hello!", pitch_shift=0.5))
print("Hello!")

# does not wait
nao.tts.request(NaoqiTextToSpeechRequest("Wereld!", pitch_shift=1.0, volume=1.5, language="Dutch", speed=50), block=False)
print("Wereld!")
