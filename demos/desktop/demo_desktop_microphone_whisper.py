# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.openai_whisper_stt.whisper_stt import (
    GetTranscript,
    SICWhisper,
    Transcript,
    WhisperConf,
)

# Import libraries necessary for the demo
import time
from os import environ
from os.path import abspath, join
from dotenv import load_dotenv


class WhisperDemo(SICApplication):
    """
    Whisper speech-to-text demo application.
    Shows how to use Whisper to transcribe your speech to text,
    either using a local model or the online OpenAI model by providing your API key.

    IMPORTANT:
    Whisper service needs to be running:
    1. pip install --upgrade social-interaction-cloud[whisper-speech-to-text]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-whisper

    NOTE: Requires you to have a secret OpenAI key.
    You can generate your personal env api key here: https://platform.openai.com/api-keys
    Put your key in a .env file in the conf/env folder as OPENAI_API_KEY="your key"
    """
    
    def __init__(self, env_path=None):
        # Call parent constructor (handles singleton initialization)
        super(WhisperDemo, self).__init__()
        
        # Demo-specific initialization
        self.desktop = None
        self.whisper = None
        self.env_path = env_path
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def on_transcript(self, message: Transcript):
        """
        Callback function for Whisper transcript results.
        
        Args:
            message: The transcript message containing the recognized text.
        
        Returns:
            None
        """
        print(message.transcript)
    
    def setup(self):
        """Initialize and configure the desktop microphone and Whisper service."""
        self.logger.info("Setting up Whisper speech-to-text...")
        
        self.desktop = Desktop()

        # Generate your personal env api key here: https://platform.openai.com/api-keys
        # Either add your env key to your systems variables (and do not provide an env_path) or
        # create a .env file in the conf/ folder and add your key there like this:
        # OPENAI_API_KEY="your key"
        if self.env_path:
            load_dotenv(self.env_path)

        whisper_conf = WhisperConf(openai_key=environ["OPENAI_API_KEY"])
        self.whisper = SICWhisper(input_source=self.desktop.mic, conf=whisper_conf)
        
        # Alternatively, use local model:
        # self.whisper = SICWhisper(input_source=self.desktop.mic)
        
        time.sleep(1)
        
        self.whisper.register_callback(self.on_transcript)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting Whisper Demo")
        
        try:
            while not self.shutdown_event.is_set():
                self.logger.info("Talk now!")
                transcript = self.whisper.request(GetTranscript(timeout=10, phrase_time_limit=30))
                self.logger.info("transcript: {transcript}".format(transcript=transcript.transcript))
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = WhisperDemo(env_path=abspath(join("..", "..", "conf", ".env")))
    demo.run()
