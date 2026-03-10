from os import environ
from os.path import abspath, join

from dotenv import load_dotenv

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.services.llm import GPT, GPTConf, GPTRequest


class GPTComplexDemo(SICApplication):
    """
    Complex GPT demo showcasing:
    - Streaming / real-time tokens
    - Chat history with explicit roles
    - Structured JSON output

    Requires a valid OpenAI API key.
    """

    def __init__(self, env_path=None):
        super(GPTComplexDemo, self).__init__()

        self.gpt = None
        self.env_path = env_path

        # Maintain full chat history as role-based messages
        self.conversation = []

        # Configure logging
        self.set_log_level(sic_logging.DEBUG)

        self.setup()

    def setup(self):
        """Initialize and configure the GPT service."""
        self.logger.info("Setting up complex GPT demo...")

        if self.env_path:
            load_dotenv(self.env_path)

        conf = GPTConf(
            openai_key=environ["OPENAI_API_KEY"],
            system_message=(
                "You are a helpful JSON-producing assistant. "
                "Always respond with a single JSON object that contains "
                "keys 'thought', 'answer', and 'metadata'."
            ),
            model="gpt-4o-mini",
            temp=0.5,
            max_tokens=200,
        )

        self.gpt = GPT(conf=conf)

        # Register callback to receive streaming chunks from the GPT component
        self.gpt.register_callback(self._on_stream_message)

    def _on_stream_message(self, message):
        """
        Callback invoked for every GPTResponse emitted by the GPT component.

        For streaming requests, intermediate chunks will have `is_stream_chunk=True`.
        """
        self.logger.debug("On stream message: %s", message)
        # Only handle GPTResponse-like messages
        if not hasattr(message, "response"):
            return

        is_chunk = getattr(message, "is_stream_chunk", False)
        finish_reason = getattr(message, "finish_reason", None)

        if is_chunk:
            # Print token chunks without newline for real-time effect
            print(message.response, end="", flush=True)

            # When the model finishes, close the line and update conversation
            if finish_reason in ("stop", "length", None):
                full = getattr(message, "full_response", None)
                if full:
                    print()  # newline after stream
                    self.conversation.append({"role": "assistant", "content": full})
        else:
            # Non-streaming replies or final summary messages
            print(message.response)
            self.conversation.append({"role": "assistant", "content": message.response})

    def run(self):
        """Main application loop."""
        self.logger.info("Starting complex GPT conversation")

        try:
            while not self.shutdown_event.is_set():
                user_input = input("You: ")
                if user_input.strip().lower() in {"exit", "quit"}:
                    break

                # Add user message to conversation history with explicit role
                self.conversation.append({"role": "user", "content": user_input})

                # Request streaming JSON-formatted response, providing full role history
                request = GPTRequest(
                    prompt=user_input,
                    role_messages=self.conversation,
                    stream=True,
                    response_format={"type": "json_object"},
                )
                
                self.logger.debug("Sending request: %s", request)

                # Send as a message (streaming handled via callback)
                self.gpt.send_message(request)

        except Exception as e:
            self.logger.error("Exception in complex GPT demo: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = GPTComplexDemo(env_path=abspath(join("..", "..", "..", "conf", ".env")))
    demo.run()

