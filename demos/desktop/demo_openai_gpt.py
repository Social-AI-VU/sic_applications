from os import environ
from os.path import abspath, join

from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest, GPTResponse
from dotenv import load_dotenv

"""

This demo shows how to use the OpenAI GPT model to get responses to user input,
and a secret API key is required to run it

IMPORTANT
OpenAI gpt service needs to be running:

1. pip install social-interaction-cloud[openai-gpt]
2. run-gpt

"""

# Generate your personal openai api key here: https://platform.openai.com/api-keys
# Either add your openai key to your systems variables (and comment the next line out) or
# create a .openai_env file in the conf/openai folder and add your key there like this:
# OPENAI_API_KEY="your key"
load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))

# Setup GPT
conf = GPTConf(openai_key=environ["OPENAI_API_KEY"])
gpt = GPT(conf=conf)

# Constants
NUM_TURNS = 5
i = 0
context = []

# Continuous conversation with GPT
while i < NUM_TURNS:
    # Ask for user input
    inp = input("Start typing...\n-->" if i == 0 else "-->")

    # Get reply from model
    reply = gpt.request(GPTRequest(inp, context_messages=context))
    print(reply.response, "\n", sep="")

    # Add user input to context messages for the model (this allows for conversations)
    context.append(inp)
    i += 1
