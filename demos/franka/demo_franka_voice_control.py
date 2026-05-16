# import basic SIC framework components
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging
from sic_framework.core.utils import extract_google_stt_transcript

# Import the device(s), service(s), and message(s) we will be using
from sic_framework.devices.common_franka.franka_motion_recorder import (
    GoHomeRequest,
    PandaJointsRecording,
    PlayRecordingRequest,
)
from sic_framework.devices.common_desktop.desktop_microphone import MicrophoneConf
from sic_framework.devices.desktop import Desktop
from sic_framework.devices.franka import Franka
from sic_framework.services.google_stt.google_stt import (
    GetStatementRequest,
    GoogleSpeechToText,
    GoogleSpeechToTextConf,
)

# Import demo-specific libraries
import json
import time
from os.path import abspath, join


class FrankaVoiceControlDemo(SICApplication):
    """
    Franka voice control demo application.
    Demonstrates controlling the Franka robot and executing prerecorded motions using voice commands via Google STT.

    IMPORTANT:
    To run this demo, you need to install the correct version of the panda-python dependency.
    A version mismatch will cause problems.
    See getting started guide for instructions:
    https://social-ai-vu.github.io/social-interaction-cloud/getting_started/getting_started_franka.html

    You will also need to have a Google Cloud API key file in the conf/google/google-key.json file.
    You will need to have the Cloud Speech-to-Text API enabled in your Google Cloud Console.
    See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html for instructions on how to get one.

    Google Speech-to-Text dependency needs to be installed and the service needs to be running:
    1. pip install --upgrade social-interaction-cloud[google-stt]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-google-stt (in a separate terminal)

    Voice commands:
    - "go home" or "home" → Robot returns to home position
    - "wave" or "waving" → Robot plays the wave motion
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(FrankaVoiceControlDemo, self).__init__()

        # Demo-specific initialization
        self.google_keyfile_path = abspath(
            join("..", "..", "conf", "google", "google-key.json")
        )
        self.motion_file = "wave.motion"
        self.num_turns = 25
        self.frequency = 1000
        self.mic_sample_rate_hz = 48000
        self.mic_device_index = 5
        self.desktop = None
        self.franka = None
        self.stt = None

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file_path("/path/to/log/directory")

        # Load environment variables
        self.load_env("../../conf/.env")
        
        self.setup()

    def on_stt(self, result):
        """
        Callback function for speech recognition results.

        Args:
            result: The speech-to-text recognition result message.

        Returns:
            None
        """
        transcript = extract_google_stt_transcript(result)
        if transcript:
            self.logger.info("Transcript: {}".format(transcript))

    def setup(self):
        """Initialize and configure Desktop, Franka, and Google STT."""
        self.logger.info("Starting Franka Voice Control Demo...")

        # Initialize devices
        mic_conf = MicrophoneConf(
            sample_rate=self.mic_sample_rate_hz,
            device_index=self.mic_device_index,
        )
        self.desktop = Desktop(mic_conf=mic_conf)
        self.franka = Franka()

        # Load the key json file
        try:
            with open(self.google_keyfile_path) as f:
                keyfile_json = json.load(f)
        except FileNotFoundError:
            self.logger.warning("No keyfile found, using None")
            keyfile_json = None

        # Set up Google STT
        stt_conf = GoogleSpeechToTextConf(
            keyfile_json=keyfile_json,
            sample_rate_hertz=self.mic_sample_rate_hz,
            language="en-US",
            interim_results=False,
        )

        self.stt = GoogleSpeechToText(conf=stt_conf, input_source=self.desktop.mic)

        self.logger.info("Initialized Google STT... registering callback function")
        # Register a callback function to act upon arrival of recognition_result
        self.stt.register_callback(callback=self.on_stt)

    def run(self):
        """Main application loop."""
        self.logger.info(" -- Starting Demo -- ")

        try:
            for i in range(self.num_turns):
                self.logger.info(" ----- Conversation turn {}".format(i))
                reply = self.stt.request(GetStatementRequest())
                query_text = extract_google_stt_transcript(reply)
                if not query_text:
                    self.logger.info("No transcript received")
                    time.sleep(0.1)
                    continue

                self.logger.info("Query text: {}".format(query_text))

                # Process voice commands
                if "home" in query_text.lower():
                    self.logger.info("Going home!")
                    self.franka.motion_recorder.request(GoHomeRequest())

                if "wave" in query_text.lower() or "waving" in query_text.lower():
                    self.logger.info("Waving!")
                    loaded_joints = PandaJointsRecording.load(self.motion_file)
                    self.logger.info("Playing wave motion")
                    self.franka.motion_recorder.request(
                        PlayRecordingRequest(loaded_joints, self.frequency)
                    )
                # Small delay between requests to allow proper cleanup
                time.sleep(0.1)

            self.logger.info("Voice control demo completed successfully")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = FrankaVoiceControlDemo()
    demo.run()
