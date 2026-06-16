r"""
Nardial RAG + LLM Conversation Demo

This demo shows how to run a Nardial conversation that uses retrieval-augmented
generation (RAG) for selected llm_based dialog blocks.

The conversation flow is defined in:
    dialog_configs/rag_llm_dialogs.json

Before running this demo, make sure you have completed the required setup steps.
This demo depends on external services for speech, language understanding, and LLM responses.
-------------------------
1. Install dependencies
-------------------------
    pip install "nardial[google-tts,dialogflow,openai]"
-------------------------
2. Configure credentials
-------------------------
You MUST create the following files:

- Dialogflow / Google credentials: conf/google/google-key.json
- OpenAI API key: conf/.env
Example `.env` entry:
    OPENAI_API_KEY="your key"

WARNING: Never commit credential files to version control.
-------------------------
3. Start required services
-------------------------
You MUST run these in separate terminals BEFORE starting the demo:
    run-redis --data-dir <path to where you want to save vector database>
    run-dialogflow
    run-google-tts
    run-gpt

NOTE: you need to have Docker installed to be able to use the RedisStack image (includes the Vector Search module) when you run 'run-redis'.
=========================
"""

import sys

# import other libraries
from pathlib import Path

# Import Nardial basics
from nardial.conversation_agent import ConversationAgent
from nardial.interaction_orchestrator import InteractionConfig
from nardial.providers.device.desktop import DesktopAdapter
from nardial.providers.llm.openai_gpt import OpenAIGPTProvider
from nardial.providers.nlu.dialogflow import DialogflowNLUProvider
from nardial.providers.tts.google import GoogleTTSConf, GoogleTTSProvider
from nardial.providers.vector_store.redis_store import RedisVectorStoreProvider
from nardial.session_manager import SessionManager

# Import SIC device(s), message(s), and service(s) we will be using
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf
from sic_framework.devices.desktop import Desktop
from sic_framework.services.dialogflow.dialogflow import DialogflowConf

BASE_DIR = Path(__file__).resolve().parent
SIC_APPLICATIONS_DIR = BASE_DIR.parents[2]

DOCS_DIR = BASE_DIR / "RAG_example_docs"
DIALOG_CONFIG_PATH = BASE_DIR / "dialog_configs" / "rag_llm_dialogs.json"
GOOGLE_KEYFILE_PATH = SIC_APPLICATIONS_DIR / "conf" / "google" / "google-key.json"
ENV_FILE_PATH = SIC_APPLICATIONS_DIR / "conf" / ".env"

INDEX_NAME = "nardial_pip_lantern_docs"
# Set to True on first run (or whenever your docs change) to re-index the RAG documents.
INGEST_DOCS = True


if __name__ == "__main__":
    # =========================
    # 1. SELECT DEVICE
    # =========================
    # Desktop uses local microphone/speakers.
    desktop = Desktop(speakers_conf=SpeakersConf(sample_rate=22050))
    device = DesktopAdapter(desktop)

    # Uncomment to use Pepper instead:
    # from nardial.providers.device.pepper import PepperAdapter
    # from sic_framework.devices import Pepper
    # device = PepperAdapter(Pepper(ip="XXX"))  # Replace with your robot's IP

    # =========================
    # 2. CONFIGURE PROVIDERS
    # =========================

    # --- TTS ---
    tts_conf = GoogleTTSConf(
        # speaking_rate=1.0,                        # speech speed (0.25–4.0)
        # google_tts_voice_name="en-US-Neural2-C",  # voice selection
    )
    tts = GoogleTTSProvider(
        conf=tts_conf, device=device, keyfile_path=str(GOOGLE_KEYFILE_PATH)
    )

    # --- NLU ---
    # device.get_mic() returns the SIC microphone component used by Dialogflow for live audio input.
    dialogflow_conf = DialogflowConf(keyfile_json=json.load(open(GOOGLE_KEYFILE_PATH)))
    nlu = DialogflowNLUProvider(conf=dialogflow_conf, mic=device.get_mic())

    # --- LLM ---
    # Reads OPENAI_API_KEY from the environment (loaded via dotenv above).
    llm = OpenAIGPTProvider()

    # --- Vector store (RAG) ---
    # Enable RAG ingestion/retrieval and point to the demo docs and index.
    # INGEST_DOCS=True indexes the documents on first run; set to False on subsequent runs
    # to skip re-ingestion and save time.
    vector_store = RedisVectorStoreProvider(
        embedding_model="text-embedding-3-large",
        index_name=INDEX_NAME,
        ingest_docs=INGEST_DOCS,
        input_path=str(DOCS_DIR),
        chunk_chars=900,
        chunk_overlap=120,
        override_existing=True,
        force_recreate_index=False,
    )

    # --- Behavioral config ---
    interaction_config = InteractionConfig(
        # language="nl",
        # post_speech_delay=0.5,
    )

    # =========================
    # 3. CREATE AGENT
    # =========================
    agent = ConversationAgent(
        device=device,
        tts_provider=tts,
        nlu_provider=nlu,
        llm_provider=llm,
        int_config=interaction_config,
        vector_store=vector_store,
    )

    # =========================
    # 4. SESSION MANAGER
    # =========================
    session_manager = SessionManager(
        session_agenda=[
            "rag_llm_welcome",
            "non_rag_warmup",
            "rag_character_backstory",
            "rag_practical_help",
            "non_rag_reflection",
            "rag_llm_goodbye",
        ],
        agent=agent,
        dialog_json_path=str(DIALOG_CONFIG_PATH),
        participant_id="1",
    )

    # =========================
    # 5. RUN SESSION
    # =========================
    session_manager.run()

    # =========================
    # 6. CLEAN EXIT
    # =========================
    sys.exit()
