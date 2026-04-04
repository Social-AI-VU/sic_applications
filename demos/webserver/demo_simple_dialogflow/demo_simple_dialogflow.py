# Import basic preliminaries
# Import libraries necessary for the demo
import json
import os
import threading
import time
import urllib.request
import webbrowser
from os.path import abspath, join
from pathlib import Path
from dotenv import load_dotenv

import numpy as np
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.core.utils import is_sic_instance
from sic_framework.core.message_python2 import AudioMessage

# Import the services we will be using
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DetectIntentRequest,
    DialogflowCX,
    DialogflowCXConf,
    StopListeningMessage,
)
from sic_framework.services.webserver.webserver_service import (
    ButtonClicked,
    TranscriptMessage,
    WebInfoMessage,
    Webserver,
    WebserverConf,
)


class DialogflowCXWebDemo(SICApplication):
    """
    Dialogflow CX (Conversational Agents) demo application using Desktop microphone for intent detection.

    IMPORTANT:
    1. You need to obtain your own keyfile.json from Google Cloud and place it in a location that the code can load.
       How to get a key? See https://social-ai-vu.github.io/social-interaction-cloud/external_apis/google_cloud.html
       Save the key in conf/google/google-key.json

    2. You need to create a Dialogflow CX agent and note:
       - Your agent ID (found in agent settings)
       - Your agent location (e.g., "global" or "us-central1")

    3. The Conversational Agents service needs to be running:
       - pip install social-interaction-cloud[dialogflow-cx]
       - run-dialogflow-cx

    Note: This uses the newer Dialogflow CX API (v3), which is different from the older Dialogflow ES (v2).
    """

    def __init__(self):
        # Call parent constructor (handles singleton initialization)
        super(DialogflowCXWebDemo, self).__init__()

        # Demo-specific initialization
        self.conversational_agent = None
        self.webserver = None
        self.web_port = 8080

        # Browser-mic control
        self.start_listening_event = threading.Event()
        self.worker_thread: threading.Thread | None = None

        self.set_log_level(sic_logging.INFO)

        # Random session ID is necessary for Dialogflow CX
        self.session_id = np.random.randint(10000)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/logs")


        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / "conf" / ".env"
        load_dotenv(env_path)
        
        self.setup()

    def setup(self):
        """Initialize web UI and Dialogflow CX service (audio via browser)."""

        # Webserver setup (serves local demo UI + receives events)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")
        web_conf = WebserverConf(
            host="0.0.0.0",
            port=self.web_port,
            templates_dir=webfiles_dir,
        )
        self.webserver = Webserver(conf=web_conf)
        self.webserver.register_callback(self.on_web_event)

        presenter_url = f"http://localhost:{self.web_port}"
        threading.Thread(target=lambda: self._open_when_ready(presenter_url), daemon=True).start()
        self.logger.info(f"Web UI: {presenter_url}")

        self.logger.info("Initializing Conversational Agents (Dialogflow CX)")

        # Load the key json file - you need to get your own keyfile.json
        with open(abspath(join("..", "..", "..", "conf", "google", "google-key.json"))) as f:
            keyfile_json = json.load(f)

        # TODO: Replace with your actual agent ID and location
        # You can find your agent ID in the Dialogflow CX console:
        # 1. Go to https://dialogflow.cloud.google.com/cx/
        # 2. Select your project
        # 3. Click on your agent
        # 4. The agent ID is in the URL: ...agents/YOUR-AGENT-ID/...
        # or in Agent Settings under "Agent ID"

        agent_id = "XXX"  # Replace with your agent ID
        location = "XXX"  # Replace with your agent location if different

        # Create configuration for Conversational Agents
        ca_conf = DialogflowCXConf(
            keyfile_json=keyfile_json,
            agent_id=agent_id,
            location=location,
            sample_rate_hertz=44100,
            language="en-US",
        )

        # Initialize the conversational agent; audio will come from the browser via Socket.IO.
        self.conversational_agent = DialogflowCX(conf=ca_conf)

        self.logger.info("Initialized Conversational Agents; starting worker thread.")
        self.worker_thread = threading.Thread(
            target=self._user_loop,
            daemon=True,
            name="dialogflow_simple_user_loop",
        )
        self.worker_thread.start()

    def _open_when_ready(self, url: str) -> None:
        ready_url = url.rstrip("/") + "/readyz"
        deadline = time.time() + 10.0
        while time.time() < deadline and not self.shutdown_event.is_set():
            try:
                with urllib.request.urlopen(ready_url, timeout=0.5) as resp:
                    if resp.status == 200:
                        webbrowser.open(url, new=2)
                        return
            except Exception:
                pass
            time.sleep(0.1)
        # Fall back to opening anyway (useful for debugging failures).
        webbrowser.open(url, new=2)

    def _publish_to_web(self, transcript: str = None, agent_response: str = None) -> None:
        if not self.webserver:
            return
        try:
            if transcript:
                self.webserver.send_message(TranscriptMessage(transcript=transcript))
            if agent_response:
                self.webserver.send_message(WebInfoMessage("agent_response", agent_response))
        except Exception as e:
            self.logger.warning(f"Failed to publish to web UI: {e}")

    def _user_loop(self) -> None:
        """Worker loop that runs Dialogflow turns when the user presses record."""
        try:
            while not self.shutdown_event.is_set():
                # Wait for the browser to send "start_audio" before starting a new turn.
                while not self.shutdown_event.is_set():
                    if self.start_listening_event.wait(timeout=0.25):
                        break
                if self.shutdown_event.is_set():
                    break
                self.start_listening_event.clear()

                self.logger.info(" ----- Conversation turn (session {})".format(self.session_id))
                try:
                    reply = self.conversational_agent.request(
                        DetectIntentRequest(self.session_id)
                    )
                except Exception as e:
                    self.logger.error("Dialogflow request failed: {}".format(e))
                    self._publish_to_web(agent_response="(error: {})".format(e))
                    time.sleep(0.5)
                    continue

                # Log the detected intent
                if reply.intent:
                    self.logger.info(
                        "The detected intent: {intent} (confidence: {conf})".format(
                            intent=reply.intent,
                            conf=(
                                reply.intent_confidence
                                if reply.intent_confidence
                                else "N/A"
                            ),
                        )
                    )
                else:
                    self.logger.info("No intent detected")

                # Log the transcript
                if reply.transcript:
                    self.logger.info("User said: {text}".format(text=reply.transcript))
                    self._publish_to_web(transcript=reply.transcript)

                # Log the agent's response
                if reply.fulfillment_message:
                    self.logger.info(
                        "Agent reply: {text}".format(text=reply.fulfillment_message)
                    )
                    self._publish_to_web(agent_response=reply.fulfillment_message)
                else:
                    self.logger.info("No fulfillment message")
                    self._publish_to_web(agent_response="(no fulfillment message)")

                # Log any parameters
                if reply.parameters:
                    self.logger.info(
                        "Parameters: {params}".format(params=reply.parameters)
                    )

                # Notify the browser that this turn is done so it can auto-stop the mic.
                try:
                    if self.webserver:
                        self.webserver.send_message(WebInfoMessage("turn_done", True))
                except Exception as e:
                    self.logger.warning(f"Failed to send turn_done to web UI: {e}")
        finally:
            try:
                if self.conversational_agent:
                    self.conversational_agent.stop_component()
            except Exception:
                pass

    def on_web_event(self, message):
        """Handle events from the web UI (start/stop + audio chunks)."""
        if not is_sic_instance(message, ButtonClicked):
            return

        data = message.button
        if not isinstance(data, dict):
            return

        event_type = str(data.get("type", "")).strip().lower()

        if event_type == "start_audio":
            # User pressed record; allow the next DetectIntentRequest to run.
            self.start_listening_event.set()
        elif event_type == "audio_chunk":
            audio_list = data.get("audio")
            if not isinstance(audio_list, list):
                return
            try:
                audio_bytes = bytes(int(b) & 0xFF for b in audio_list)
            except Exception as e:
                self.logger.warning(f"Invalid audio payload from browser: {e}")
                return

            sample_rate = int(data.get("sample_rate") or 44100)
            try:
                if self.conversational_agent:
                    self.conversational_agent.send_message(
                        AudioMessage(audio_bytes, sample_rate=sample_rate)
                    )
            except Exception as e:
                self.logger.error(f"Failed to forward audio chunk to Dialogflow: {e}")
        elif event_type == "stop_audio":
            try:
                if self.conversational_agent:
                    self.conversational_agent.send_message(
                        StopListeningMessage(session_id=self.session_id)
                    )
            except Exception as e:
                self.logger.error(f"Failed to send StopListeningMessage: {e}")

    def run(self):
        """Main application loop (idle; work is done in background worker)."""
        self.logger.info(" -- Starting Conversational Agents Demo -- ")

        try:
            while not self.shutdown_event.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = DialogflowCXWebDemo()
    demo.run()
