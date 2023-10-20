from sic_framework.core.message_python2 import TextRequest
from sic_framework.devices.common_desktop.desktop_text_to_speech import TextToSpeechConf
from sic_framework.devices.desktop import Desktop

""" 
This demo should make your laptop say "Hello world!" with a robotic voice.
"""

tts_conf = TextToSpeechConf(rate=160, pitch=55)

desktop = Desktop(tts_conf=tts_conf)

desktop.tts.request(TextRequest("Hello world!"))

