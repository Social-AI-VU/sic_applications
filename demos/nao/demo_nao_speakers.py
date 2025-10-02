"""
This script demonstrates how to use the Nao speakers to play a wav file.
"""

import wave

from sic_framework.core.message_python2 import AudioMessage, AudioRequest
from sic_framework.devices import Nao
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# In case you want to use the logger with a neat format as opposed to logger.info statements.
app = SICApplication()
logger = app.get_app_logger()

# can be DEBUG, INFO, WARNING, ERROR, CRITICAL
app.set_log_level(sic_logging.DEBUG)

# Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
# app.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

# Use the shutdown event as a loop condition.
shutdown_flag = app.get_shutdown_event()

# Read the wav file
wavefile = wave.open("test_sound_dialogflow.wav", "rb")
samplerate = wavefile.getframerate()

logger.info("Audio file specs:")
logger.info("  sample rate: {}".format(wavefile.getframerate()))
logger.info("  length: {}".format(wavefile.getnframes()))
logger.info("  data size in bytes: {}".format(wavefile.getsampwidth()))
logger.info("  number of channels: {}".format(wavefile.getnchannels()))
logger.info("")


try:
    logger.info("Starting Nao Speakers Demo...")
    # nao = Nao(ip="XXX")
    # nao = Nao(ip="10.0.0.241", dev_test=True, test_repo="/Users/apple/Desktop/SAIL/SIC_Development/social-interaction-cloud")
    nao = Nao(ip="10.0.0.241", dev_test=True)

    logger.info("Sending audio!")
    sound = wavefile.readframes(wavefile.getnframes())
    message = AudioRequest(sample_rate=samplerate, waveform=sound)
    nao.speaker.request(message)

    logger.info("Audio sent, without waiting for it to complete playing.")
    logger.info("Speakers demo completed successfully")
except Exception as e:
    logger.error("Error in speakers demo: {e}".format(e=e))
finally:
    wavefile.close()
    logger.info("Shutting down application")
    app.shutdown()
