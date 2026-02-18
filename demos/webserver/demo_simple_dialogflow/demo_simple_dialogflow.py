# Import basic preliminaries
# Import libraries necessary for the demo
import json
import os
import threading
import time
import urllib.request
import webbrowser
from os.path import abspath, join

import numpy as np
from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication

# Import the device(s) we will be using
from sic_framework.devices.desktop import Desktop

# Import the service(s) we will be using
from sic_framework.services.dialogflow_cx.dialogflow_cx import (
    DetectIntentRequest,
    DialogflowCX,
    DialogflowCXConf,
)
from sic_framework.services.webserver.webserver_service import (
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
        self.desktop = None
        self.desktop_mic = None
        self.conversational_agent = None
        self.webserver = None
        self.web_port = 8080

        self.set_log_level(sic_logging.DEBUG)

        # Random session ID is necessary for Dialogflow CX
        self.session_id = np.random.randint(10000)

        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")

        self.setup()

    def on_recognition(self, message):
        """
        Callback function for Dialogflow CX recognition results.

        Args:
            message: The Dialogflow CX recognition result message.

        Returns:
            None
        """
        if message.response:
            if (
                hasattr(message.response, "recognition_result")
                and message.response.recognition_result
            ):
                rr = message.response.recognition_result
                if hasattr(rr, "is_final") and rr.is_final:
                    if hasattr(rr, "transcript"):
                        self.logger.info(
                            "Transcript: {transcript}".format(transcript=rr.transcript)
                        )

    def setup(self):
        """Initialize and configure the desktop microphone and Conversational Agents service."""
        self.logger.info("Initializing Desktop microphone")

        # Local desktop setup
        self.desktop = Desktop()
        self.desktop_mic = self.desktop.mic

        # Webserver setup (serves local demo UI + receives events)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        webfiles_dir = os.path.join(current_dir, "webfiles")
        web_conf = WebserverConf(
            host="0.0.0.0",
            port=self.web_port,
            templates_dir=webfiles_dir,
        )
        self.webserver = Webserver(conf=web_conf)

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

        agent_id = "27cdbb58-604e-4da9-bb34-91bb7bc62883"  # Replace with your agent ID
        location = "europe-west4"  # Replace with your agent location if different

        # Create configuration for Conversational Agents
        ca_conf = DialogflowCXConf(
            keyfile_json=keyfile_json,
            agent_id=agent_id,
            location=location,
            sample_rate_hertz=44100,
            language="en-US",
        )

        # Initialize the conversational agent with microphone input
        self.conversational_agent = DialogflowCX(
            conf=ca_conf, input_source=self.desktop_mic
        )

        self.logger.info(
            "Initialized Conversational Agents... registering callback function"
        )
        # Register a callback function to handle recognition results
        self.conversational_agent.register_callback(callback=self.on_recognition)

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

    def run(self):
        """Main application loop."""
        self.logger.info(" -- Starting Conversational Agents Demo -- ")

        try:
            while not self.shutdown_event.is_set():
                self.logger.info(" ----- Conversation turn")

                # Request intent detection with the current session
                reply = self.conversational_agent.request(
                    DetectIntentRequest(self.session_id)
                )

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

        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
            import traceback

            traceback.print_exc()
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    demo = DialogflowCXWebDemo()
    demo.run()
