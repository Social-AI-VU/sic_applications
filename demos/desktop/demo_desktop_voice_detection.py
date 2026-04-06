# Import basic preliminaries
# Import libraries necessary for the demo
import time

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.voice_detection.voice_detection import (
    VoiceDetection,
    VoiceDetectionConf,
    VoiceDetectionMessage,
)


class VoiceDetectionDemo(SICApplication):
    """
    Voice Detection demo application.
    Shows how to use VoiceDetection service with Silero VAD to detect when someone is speaking.

    IMPORTANT:
    VoiceDetection service needs to be running:
    1. pip install torch torchaudio numpy
    2. run-voice-detection (or start the service manually)

    The service uses Silero VAD model which will be automatically downloaded on first use.
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(VoiceDetectionDemo, self).__init__()

        # Demo-specific initialization
        self.desktop = None
        self.voice_detection = None

        # Configure logging
        self.set_log_level(sic_logging.INFO)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log")


        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def on_voice_detection(self, message: VoiceDetectionMessage):
        """
        Callback function for VoiceDetection results.
        Logs when someone starts or stops speaking.

        Args:
            message: The voice detection message containing the speech state.

        Returns:
            None
        """
        if message.is_speaking:
            self.logger.info(
                "Someone is speaking! (speech proportion: {:.2f})".format(
                    message.speech_proportion
                )
            )
        else:
            self.logger.info("No one is speaking")

    def setup(self):
        """Initialize and configure the desktop microphone and VoiceDetection service."""
        self.logger.info("Setting up Voice Detection service...")

        self.desktop = Desktop()

        # Create voice detection configuration with default settings
        # You can customize these parameters:
        # - threshold: Speech probability threshold (default: 0.5)
        # - sampling_rate: Expected audio sample rate (default: 16000)
        # - min_speech_duration_ms: Minimum speech duration (default: 250)
        # - min_silence_duration_ms: Minimum silence duration (default: 100)
        # - message_frequency: Number of times per second to output messages regardless of state change (0 = only on state change).
        voice_detection_conf = VoiceDetectionConf()
        self.voice_detection = VoiceDetection(
            input_source=self.desktop.mic, conf=voice_detection_conf
        )

        time.sleep(1)

        self.voice_detection.register_callback(self.on_voice_detection)
        self.logger.info(
            "Voice Detection service is ready. Start speaking to see detection results!"
        )

    def run(self):
        """Main application loop."""
        self.logger.info("Starting Voice Detection Demo")
        self.logger.info("The demo will continuously monitor for speech activity.")
        self.logger.info("Press Ctrl+C to stop.")

        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.1)  # Keep the main thread alive
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = VoiceDetectionDemo()
    demo.run()
