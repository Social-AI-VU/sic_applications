# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the message type(s) we're using
from sic_framework.devices.common_desktop.desktop_text_to_speech import TextToSpeechConf
from sic_framework.core.message_python2 import TextRequest


class DesktopTTSDemo(SICApplication):
    """
    Simple desktop TTS demo application.

    This demo shows how to use the Desktop TTS component to speak text
    with custom configuration.

    IMPORTANT:
    espeak needs to be installed.
    [Windows]
    download and install espeak: http://espeak.sourceforge.net/
    add eSpeak/command-line to PATH
    [Linux]
    `sudo apt-get install espeak libespeak-dev`
    [MacOS]
    brew install espeak
    """
    
    def __init__(self):
        # Call parent constructor
        super(DesktopTTSDemo, self).__init__()
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        
        # Create TTS configuration
        # amplitude: Volume (0-200), default 100
        # pitch: Pitch adjustment (0-99), default 50
        # speed: Speed in words per minute, default 175
        # gap: Word gap in 10ms units, default 0
        # voice: Voice to use (e.g., 'en', 'en-us', 'en+f3'), default 'en'
        self.tts_conf = TextToSpeechConf(
            amplitude=120,    # A bit louder
            pitch=50,         # Normal pitch
            speed=160,        # Slightly slower for clarity
            gap=0,            # No gap between words
            voice="en"        # English voice
        )
        self.desktop = None

        self.setup()

    def setup(self):
        
        # Initialize desktop device with TTS configuration
        self.desktop = Desktop(tts_conf=self.tts_conf)
        self.tts = self.desktop.tts
        
        self.logger.info("Desktop TTS Demo initialized with custom configuration")
    
    def run(self):
        """Main application loop - speak some text."""
        self.logger.info("Starting TTS demo")
        
        try:
            # List of things to say
            phrases = [
                "Hello! I am a desktop text to speech system.",
                "I use espeak to convert text to speech.",
                "This is a simple demonstration.",
                "Thank you for listening!"
            ]
            
            # Speak each phrase
            for phrase in phrases:
                self.logger.info("Speaking: {}".format(phrase))
                response = self.tts.request(TextRequest(phrase))
                self.logger.info("Finished speaking")
            
            self.logger.info("Demo complete")
            
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = DesktopTTSDemo()
    demo.run()

