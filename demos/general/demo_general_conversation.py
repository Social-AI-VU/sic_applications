# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop
from sic_framework.devices import Nao
from sic_framework.devices.alphamini import Alphamini

# Import the service(s) we will be using
from sic_framework.services.dialogflow.dialogflow import (
    Dialogflow,
    DialogflowConf,
    GetIntentRequest,
)
from sic_framework.services.google_tts.google_tts import (
    Text2Speech,
    Text2SpeechConf,
    GetSpeechRequest,
    SpeechResult
)
from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest

# Import configuration and message types
from sic_framework.devices.common_mini.mini_speaker import MiniSpeakersConf
from sic_framework.core.message_python2 import AudioRequest

# Import libraries necessary for the demo
import json
import wave
from os import environ
from os.path import abspath, join
import numpy as np
from dotenv import load_dotenv


class ConversationDemo(SICApplication):
    """
    General conversation demo application.
    Demonstrates an agent-driven conversation utilizing Google Dialogflow, Google TTS, and OpenAI's GPT.

    IMPORTANT:
    1. Set-up Google Cloud Console with Dialogflow and Google TTS:
       Create a keyfile: https://social-ai-vu.github.io/social-interaction-cloud/tutorials/6_google_cloud.html
       Save it as conf/google/google-key.json

    2. Configure your Dialogflow agent:
       a. Remove all default intents
       b. Go to settings -> import and export -> import the droomrobot_dialogflow_agent.zip

    3. You need an OpenAI key:
       Generate key here: https://platform.openai.com/api-keys
       Create a .openai_env file in conf/openai folder with: OPENAI_API_KEY="your key"

    4. Services need to be running:
       pip install --upgrade social-interaction-cloud[dialogflow,google-tts,openai-gpt,alphamini]
       run-dialogflow (in new terminal)
       run-google-tts (in new terminal)
       run-gpt (in new terminal)
    """
    def __init__(self, google_keyfile_path, sample_rate_dialogflow_hertz=44100, dialogflow_language="en",
                 google_tts_voice_name="en-US-Standard-C", google_tts_voice_gender="FEMALE", default_speaking_rate=1.0,
                 openai_key_path=None):
        # Call parent constructor (handles singleton initialization)
        super(ConversationDemo, self).__init__()
        
        # Demo-specific initialization
        self.google_keyfile_path = google_keyfile_path
        self.sample_rate_dialogflow_hertz = sample_rate_dialogflow_hertz
        self.dialogflow_language = dialogflow_language
        self.google_tts_voice_name = google_tts_voice_name
        self.google_tts_voice_gender = google_tts_voice_gender
        self.default_speaking_rate = default_speaking_rate
        self.openai_key_path = openai_key_path
        
        self.gpt = None
        self.dialogflow = None
        self.tts = None
        self.tts_sample_rate = None
        self.request_id = np.random.randint(10000)
        self.device = None
        self.mic = None
        self.speaker = None

        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/general/logs")
        
        self.setup()
        
    def setup(self):
        """Initialize and configure GPT, Dialogflow, and Google TTS."""
        self.logger.info("Setting up Conversation Demo...")
        
        # Load OpenAI API key
        if self.openai_key_path:
            load_dotenv(self.openai_key_path)

        # Setup GPT client
        conf = GPTConf(openai_key=environ["OPENAI_API_KEY"])
        self.gpt = GPT(conf=conf)
        self.logger.info("OpenAI GPT Ready")

        # Set up the config for dialogflow
        dialogflow_conf = DialogflowConf(
            keyfile_json=json.load(open(self.google_keyfile_path)),
            sample_rate_hertz=self.sample_rate_dialogflow_hertz,
            language=self.dialogflow_language
        )

        # Initiate Dialogflow object (without input source initially)
        self.dialogflow = Dialogflow(ip="localhost", conf=dialogflow_conf)
        self.logger.info("Dialogflow Ready")

        # Initialize TTS
        self.tts = Text2Speech(
            conf=Text2SpeechConf(
                keyfile=self.google_keyfile_path,
                speaking_rate=self.default_speaking_rate
            )
        )
        init_reply = self.tts.request(
            GetSpeechRequest(
                text="I am initializing",
                voice_name=self.google_tts_voice_name,
                ssml_gender=self.google_tts_voice_gender
            )
        )
        self.tts_sample_rate = init_reply.sample_rate
        self.logger.info("Google TTS ready")
        
    def connect_device(self, device):
        """
        Connect a device (Desktop, NAO, Alphamini, etc.) to the conversation system.
        
        Args:
            device: The device to connect (must have mic and speaker/speakers).
        """
        self.device = device
        self.mic = device.mic
        self.dialogflow.connect(self.mic)
        self.logger.info("Device connected")
        
        # Desktop uses 'speakers', robots use 'speaker'
        if isinstance(device, Desktop):
            self.speaker = device.speakers
        else:
            self.speaker = device.speaker

    def say(self, text, speaking_rate=1.0):
        """
        Synthesize and play speech using Google TTS.
        
        Args:
            text: The text to speak.
            speaking_rate: The speaking rate (default: 1.0).
        """
        self.logger.info("Saying: {}".format(text))
        reply = self.tts.request(
            GetSpeechRequest(
                text=text,
                voice_name=self.google_tts_voice_name,
                ssml_gender=self.google_tts_voice_gender,
                speaking_rate=speaking_rate
            )
        )
        self.logger.debug("Speech generated with sample rate: {}".format(reply.sample_rate))
        self.speaker.request(AudioRequest(reply.waveform, reply.sample_rate))
        self.logger.debug("Sent to device speaker")

    def play_audio(self, audio_file):
        with wave.open(audio_file, 'rb') as wf:
            # Get parameters
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()

            # Ensure format is 16-bit (2 bytes per sample)
            if sample_width != 2:
                raise ValueError("WAV file is not 16-bit audio. Sample width = {} bytes.".format(sample_width))

            self.speaker.request(AudioRequest(wf.readframes(n_frames), framerate))

    def ask_yesno(self, question, max_attempts=2):
        attempts = 0
        while attempts < max_attempts:
            # ask question
            tts_reply = self.tts.request(GetSpeechRequest(text=question,
                                                          voice_name=self.google_tts_voice_name,
                                                          ssml_gender=self.google_tts_voice_gender))
            self.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))

            # listen for answer
            reply = self.dialogflow.request(GetIntentRequest(self.request_id, {'answer_yesno': 1}))

            print("The detected intent:", reply.intent)

            # return answer
            if reply.intent:
                if "yesno_yes" in reply.intent:
                    return "yes"
                elif "yesno_no" in reply.intent:
                    return "no"
                elif "yesno_dontknow" in reply.intent:
                    return "dontknow"
            attempts += 1
        return None

    def ask_entity(self, question, context, target_intent, target_entity, max_attempts=2):
        attempts = 0

        while attempts < max_attempts:
            # ask question
            tts_reply = self.tts.request(GetSpeechRequest(text=question,
                                                          voice_name=self.google_tts_voice_name,
                                                          ssml_gender=self.google_tts_voice_gender))
            self.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))

            # listen for answer
            reply = self.dialogflow.request(GetIntentRequest(self.request_id, context))

            print("The detected intent:", reply.intent)

            # Return entity
            if reply.intent:
                if target_intent in reply.intent:
                    if reply.response.query_result.parameters and target_entity in reply.response.query_result.parameters:
                        return reply.response.query_result.parameters[target_entity]
            attempts += 1
        return None

    def ask_open(self, question, max_attempts=2):
        attempts = 0

        while attempts < max_attempts:
            # ask question
            tts_reply = self.tts.request(GetSpeechRequest(text=question,
                                                          voice_name=self.google_tts_voice_name,
                                                          ssml_gender=self.google_tts_voice_gender))
            self.speaker.request(AudioRequest(tts_reply.waveform, tts_reply.sample_rate))

            # listen for answer
            reply = self.dialogflow.request(GetIntentRequest(self.request_id))

            print("The detected intent:", reply.intent)

            # Return entity
            if reply.response.query_result.query_text:
                return reply.response.query_result.query_text
            attempts += 1
        return None

    def personalize(self, robot_input, user_age, user_input):
        """
        Generate a personalized response using GPT based on user context.
        
        Args:
            robot_input: What the robot just asked.
            user_age: Age of the user.
            user_input: What the user said.
        
        Returns:
            Personalized response text.
        """
        gpt_response = self.gpt.request(
            GPTRequest(
                f'Je bent een sociale robot die praat met een kind van {str(user_age)} jaar oud.'
                f'Het kind ligt in het ziekenhuis.'
                f'Jij bent daar om het kind af te leiden met een leuk gesprek.'
                f'Als robot heb je zojuist het volgende gevraagd: {robot_input}'
                f'Het kind reageerde met het volgende: "{user_input}"'
                f'Genereer nu een passende reactie in 1 zin.'
            )
        )
        return gpt_response.response

    def run(self):
        """Main application logic."""
        try:
            self.say("Hello, I am your companion robot")
            self.logger.info("Conversation demo completed")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == '__main__':
    # Create the conversation demo
    demo = ConversationDemo(
        google_keyfile_path=abspath(join("..", "..", "conf", "google", "google-key.json")),
        openai_key_path=abspath(join("..", "..", "conf", "openai", ".openai_env"))
    )

    # Select your device (uncomment the one you want to use)
    desktop = Desktop()
    # nao = Nao(ip="xxx.xxx.xxx.xxx")
    # alphamini = Alphamini(ip="xxx.xxx.xxx.xxx", mini_id="00xxx", mini_password="alphago", 
    #                       redis_ip="yyy.yyy.yyy.yyy",
    #                       speaker_conf=MiniSpeakersConf(sample_rate=demo.tts_sample_rate))

    demo.connect_device(desktop)
    demo.run()

