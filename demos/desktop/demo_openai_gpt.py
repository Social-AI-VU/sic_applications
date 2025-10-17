# Import basic preliminaries
from sic_framework.core.sic_application import SICApplication
from sic_framework.core import sic_logging

# Import the OpenAI GPT service, configuration, and message types
from sic_framework.services.openai_gpt.gpt import (
    GPT, 
    GPTConf, 
    GPTRequest, 
    GPTResponse
)

# Import libraries necessary for the demo
from os.path import abspath, join
from dotenv import load_dotenv
from os import environ

class GPTDemo(SICApplication):
    """
    Demo which shows how to use the OpenAI GPT model to get responses to user input.

    A secret API key is required to run it.

    IMPORTANT
    OpenAI GPT service needs to be running:

    1. pip install --upgrade social-interaction-cloud[openai-gpt]
        Note: on macOS you might need use quotes pip install --upgrade "social-interaction-cloud[...]"
    2. run-gpt
    """
    
    def __init__(self, env_path=None):
        # Call parent constructor (handles singleton initialization)
        super(GPTDemo, self).__init__()
        
        # Demo-specific initialization
        self.gpt = None
        self.env_path = env_path
        self.context = []
        self.NUM_TURNS = 5
        
        # Configure logging
        self.set_log_level(sic_logging.INFO)
        
        # Log files will only be written if set_log_file is called. Must be a valid full path to a directory.
        # self.set_log_file("/Users/apple/Desktop/SAIL/SIC_Development/sic_applications/demos/desktop/logs")
        
        self.setup()
    
    def setup(self):
        """Initialize and configure the GPT service."""
        self.logger.info("Setting up GPT...")
        
        # Generate your personal env api key here: https://platform.openai.com/api-keys
        # Either add your env key to your systems variables (and do not provide an env_path) or
        # create a .env file in the conf/ folder and add your key there like this:
        # OPENAI_API_KEY="your key"
        if self.env_path:
            load_dotenv(self.env_path)
        
        # Setup GPT
        # To see all available models, see https://platform.openai.com/docs/models and https://platform.openai.com/docs/api-reference/models/list
        # You may have to make a GET request to https://api.openai.com/v1/models (using curl or postman) to see all available models and their names.
        conf = GPTConf(
            openai_key=environ["OPENAI_API_KEY"],
            system_message="You are a rhyming poet. Answer every question with a rhyme.",
            model="gpt-4o-mini",
            temp=0.5,
            max_tokens=100
        )
        
        self.gpt = GPT(conf=conf)
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting GPT conversation")
        
        i = 0
        
        # Continuous conversation with GPT
        try:
            while not self.shutdown_event.is_set() and i < self.NUM_TURNS:
                # Ask for user input
                user_input = input("Start typing...\n-->" if i == 0 else "-->")
                
                # Get reply from model
                # You can also override the parameters set in the conf within the request, but it is optional
                # Here we add an additional system message to the request (system messages compound with the one in the conf)
                # At the very least, you need to pass in an input, and likely also the context messages.
                reply = self.gpt.request(GPTRequest(input=user_input, context_messages=self.context, system_message="Reverse the order of everything you say."))
                print("Reply: {response}".format(response=reply.response))
                
                # Add user input to context messages for the model (this allows for conversations)
                self.context.append(user_input)
                i += 1
            
            self.logger.info("Conversation ended")
        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        finally:
            self.shutdown()


if __name__ == "__main__":
    # Create and run the demo
    # This will be the single SICApplication instance for the process
    demo = GPTDemo(env_path=abspath(join("..", "..", "conf", ".env")))
    demo.run()
