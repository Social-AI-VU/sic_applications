"""

This demo shows how to use the OpenAI GPT model to get responses to user input,
and a secret API key is required to run it

IMPORTANT
OpenAI gpt service needs to be running:

1. pip install social-interaction-cloud[openai-gpt]
2. run-gpt

"""

from os import environ
from os.path import abspath, join

from sic_framework.services.openai_gpt.gpt import GPT, GPTConf, GPTRequest, GPTResponse
from dotenv import load_dotenv


# Generate your personal openai api key here: https://platform.openai.com/api-keys
# Either add your openai key to your systems variables (and comment the next line out) or
# create a .openai_env file in the conf/openai folder and add your key there like this:
# OPENAI_API_KEY="your key"
load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))

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

gpt = GPT(conf=conf)

# Constants
NUM_TURNS = 5
i = 0
context = []

# Continuous conversation with GPT
while i < NUM_TURNS:
    # Ask for user input
    user_input = input("Start typing...\n-->" if i == 0 else "-->")

    # Get reply from model
    # You can also override the parameters set in the conf within the request, but it is optional
    # Here we add an additional system message to the request (system messages compound with the one in the conf)
    # At the very least, you need to pass in an input, and likely also the context messages
    reply = gpt.request(GPTRequest(input=user_input, context_messages=context, system_message="Reverse the order of everything you say."))
    print(reply.response, "\n", sep="")

    # Add user input to context messages for the model (this allows for conversations)
    context.append(user_input)
    i += 1