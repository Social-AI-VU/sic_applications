from os import environ
from os.path import abspath, join

from dotenv import load_dotenv

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.services.llm import GPT, GPTConf, GPTRequest


class ChatGPTDemo(SICApplication):
    """
    ChatGPT demo showcasing:
    - Simple non-streaming request/response
    - Streaming / real-time tokens via callbacks
    - Conversation history with explicit roles

    Requires a valid OpenAI API key.

    IMPORTANT
    OpenAI GPT service needs to be running:

    1. pip install --upgrade social-interaction-cloud[openai-gpt]
       Note: on macOS you might need to use quotes:
       pip install --upgrade "social-interaction-cloud[openai-gpt]"
    2. run-gpt
    """

    def __init__(self, env_path=None):
        super(ChatGPTDemo, self).__init__()

        self.gpt = None
        self.env_path = env_path

        # Maintain full chat history as role-based messages
        self.conversation = []

        # Configure logging
        self.set_log_level(sic_logging.INFO)

        self.setup()

    def setup(self):
        """Initialize and configure the GPT service."""
        self.logger.info("Setting up unified GPT demo...")

        if self.env_path:
            load_dotenv(self.env_path)

        # This configuration is streaming-capable; whether a *request* actually
        # streams is controlled per-request via GPTRequest.stream.
        conf = GPTConf(
            openai_key=environ["OPENAI_API_KEY"],
            system_message="You are a helpful assistant.",
            model="gpt-4o-mini",
            temp=0.5,
            max_tokens=200,
            response_format=None,
        )

        self.gpt = GPT(conf=conf)

        # Register callback to receive streaming chunks from the GPT component
        self.gpt.register_callback(self._on_stream_message)

    def _on_stream_message(self, message):
        """
        Callback invoked for every GPTResponse emitted by the GPT component.

        For streaming requests, intermediate chunks will have `is_stream_chunk=True`.
        """
        # Only handle GPTResponse-like messages
        if not hasattr(message, "response"):
            return

        is_chunk = getattr(message, "is_stream_chunk", False)

        if is_chunk:
            # Stream raw text chunks as they arrive, but collapse any model-inserted
            # newlines so the answer appears on a single terminal line.
            chunk_text = message.response.replace("\n", " ")
            print(chunk_text, end="", flush=True)
        else:
            # print a newline after the full response
            print()

    def run(self):
        """
        Main application loop.

        At startup, you choose whether to use:
        - simple non-streaming request/response, or
        - streaming with real-time tokens.
        That choice then applies to the whole conversation.
        """
        self.logger.info("Starting unified GPT conversation")

        # Choose mode once at the start
        mode = None
        while mode not in {"s", "t"} and not self.shutdown_event.is_set():
            mode = input("Choose mode: [s]imple or [t]reaming (q to quit): ").strip().lower()
            if mode in {"quit", "q", "exit"}:
                return

        streaming = mode == "t"

        try:
            while not self.shutdown_event.is_set():
                user_input = input("You: ")
                if user_input.strip().lower() in {"exit", "quit"}:
                    break

                # Add user message to conversation history with explicit role
                self.conversation.append({"role": "user", "content": user_input})

                # Shared base request using role-based history
                base_request_kwargs = {
                    "prompt": user_input,
                    "role_messages": self.conversation,
                }

                if not streaming:
                    # Simple, non-streaming request/response
                    request = GPTRequest(
                        **base_request_kwargs,
                        stream=False,
                    )
                    self.logger.debug("Sending non-streaming request: %s", request)
                    reply = self.gpt.request(request)
                    print("AI:", reply.response)
                    self.conversation.append({"role": "assistant", "content": reply.response})
                else:
                    # Streaming request: chunks will be delivered to _on_stream_message
                    request = GPTRequest(
                        **base_request_kwargs,
                        stream=True,
                    )
                    self.logger.debug("Sending streaming request: %s", request)
                    print("AI: ", end="", flush=True)
                    reply = self.gpt.request(request)
                    # Store the full assistant message for context
                    self.conversation.append({"role": "assistant", "content": reply.response})

        except Exception as e:
            self.logger.error("Exception in unified GPT demo: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = ChatGPTDemo(env_path=abspath(join("..", "..", "conf", ".env")))
    demo.run()