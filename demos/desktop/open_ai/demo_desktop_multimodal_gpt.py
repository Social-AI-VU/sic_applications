from os import environ
from os.path import abspath, join

from dotenv import load_dotenv

from sic_framework.core import sic_logging
from sic_framework.core.sic_application import SICApplication
from sic_framework.services.llm import GPT, GPTConf, GPTRequest


class GPTMultimodalDemo(SICApplication):
    """
    Multimodal GPT demo showcasing text + image inputs.

    The demo asks for an image URL and a question about that image, and then
    sends both as a single multimodal request to the GPT service.
    """

    def __init__(self, env_path=None):
        super(GPTMultimodalDemo, self).__init__()

        self.gpt = None
        self.env_path = env_path

        # Configure logging
        self.set_log_level(sic_logging.INFO)

        self.setup()

    def setup(self):
        """Initialize and configure the GPT service."""
        self.logger.info("Setting up multimodal GPT demo...")

        if self.env_path:
            load_dotenv(self.env_path)

        conf = GPTConf(
            openai_key=environ["OPENAI_API_KEY"],
            system_message=(
                "You are a helpful vision-language assistant. "
                "Use both the image and the user's question to answer."
            ),
            model="gpt-4o-mini",
            temp=0.3,
            max_tokens=200,
        )

        self.gpt = GPT(conf=conf)

    def run(self):
        """Single-turn multimodal interaction."""
        self.logger.info("Starting multimodal GPT interaction")

        try:
            image_url = input("Enter an image URL (or 'quit' to exit): ").strip()
            if image_url.lower() in {"quit", "exit"}:
                return

            question = input("Describe what you want to know about the image:\nYou: ").strip()
            if not question:
                self.logger.info("No question provided, exiting.")
                return

            reply = self.gpt.request(
                GPTRequest(
                    prompt=question,
                    image_urls=[image_url],
                )
            )
            print("Model:", reply.response)

        except Exception as e:
            self.logger.error("Exception in multimodal GPT demo: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    demo = GPTMultimodalDemo(env_path=abspath(join("..", "..", "conf", ".env")))
    demo.run()

