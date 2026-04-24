import sys
from os.path import abspath, dirname, join

from sic_framework.devices import Pepper
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop

from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.session_manager import SessionManager

"""
=========================
Demo - Pre-run Setup
=========================
Before running this demo, make sure you have completed the required setup steps.
This demo depends on external services for speech, language understanding, and LLM responses.
-------------------------
1. Install dependencies
-------------------------
From the repository root:
    pip install -e .
    pip install --upgrade social-interaction-cloud[dialogflow,google-tts,openai-gpt]
-------------------------
2. Configure credentials
-------------------------
You MUST create the following files:

- Dialogflow / Google credentials: conf/google/google_keyfile.json
- OpenAI API key: conf/openai/.openai_env
Example `.openai_env` file:
    OPENAI_API_KEY="your key"

WARNING: Never commit these files to version control.
-------------------------
3. Start required services
-------------------------
You MUST run these in separate terminals BEFORE starting the demo:

    conf/redis/redis-server.exe conf/redis/redis.conf
    run-dialogflow
    run-google-tts
    run-gpt
=========================
"""

# Path to your Google credentials (used for speech recognition + TTS if using Google)
# You can replace this with your own path or environment-based config
google_keyfile_path = join("..", "..", "conf", "google", "google-key.json")

if __name__ == '__main__':
    # =========================
    # 1. SELECT DEVICE
    # =========================
    # Choose where the conversation runs:
    # - Desktop: uses your computer's mic + speakers
    # - Pepper: connects to a Pepper robot (requires IP)

    device = Desktop(
        speakers_conf=SpeakersConf(
            sample_rate=22050  # You can change audio quality (higher = better, but heavier)
        )
    )

    # Uncomment to use Pepper instead:
    # device = Pepper(ip="10.0.0.148")  # Replace with your robot's IP

    # =========================
    # 2. CONFIGURE INTERACTION
    # =========================
    # This controls language, speech, APIs, and behavior

    interaction_config = InteractionConfig(
        google_keyfile_path=google_keyfile_path,
        keyboard_input=True

        # Change language (affects ASR + TTS + dialogflow)
        # language="nl",

        # Optional: specify microphone manually
        # microphone_device=1,

        # Optional: path to OpenAI key (if not using default location)
        # openai_key_path="path/to/.openai_env",

        # Add a pause after the agent speaks (seconds)
        # post_speech_delay=0.5,

        # Visual/behavior cue while listening (useful for robots)
        # signal_listening_behavior=True,
    )

    # ADVANCED (inside InteractionConfig defaults):
    # - Change voice via GoogleTTSConf (voice name, speaking_rate)
    # - animated = True -> enable gestures (for embodied agents)
    # - always_regenerate = True -> disable audio caching
    # - chunk_audio = True -> stream audio in chunks (lower latency)

    # =========================
    # 3. CREATE AGENT
    # =========================
    # The agent combines device + interaction config
    agent = ConversationAgent(
        device_manager=device,
        int_config=interaction_config
    )

    # =========================
    # 4. DEFINE SESSION STRUCTURE
    # =========================
    # This determines the flow of the conversation.
    # Each string must match a dialog_id in your JSON file.

    session_agenda = [
        "welcome_and_name",  # greeting + collect user name
        "plan_activity",  # collaborative planning
        "adapt_to_user_energy",  # dynamic behavior based on user state
        "structured_goodbye",  # closing the interaction
    ]

    # You can:
    # - Reorder steps to change flow
    # - Remove items for shorter sessions
    # - Add new dialog_ids from your dialog JSON

    # =========================
    # 5. SESSION MANAGER
    # =========================
    # Handles dialog execution, state tracking, and logging

    session_manager = SessionManager(
        session_agenda=session_agenda,

        agent=agent,

        # Path to your dialog definitions
        dialog_json_path="dialog_configs/structured_conversation_dialogs.json",

        # Optional: identify the user (used for personalization/memory)
        participant_id="2",
    )

    # Internally, SessionManager:
    # - Loads dialogs from JSON
    # - Filters them based on eligibility (DialogLogic)
    # - Tracks conversation state (topics, completed dialogs)
    # - Logs session history
    # - Extracts topics of interest using GPT

    # =========================
    # 6. RUN SESSION
    # =========================
    # Starts the full interaction loop

    session_manager.run()

    # =========================
    # 7. CLEAN EXIT
    # =========================
    sys.exit()