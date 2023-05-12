from sic_framework.devices.common_naoqi.naoqi_speakers import NaoqiTextToSpeech, NaoqiTextToSpeechRequest

nao_tts = NaoqiTextToSpeech(ip='192.168.0.151')
nao_tts.request(NaoqiTextToSpeechRequest("Hello!"))