from sic_framework import SICComponentManager, SICConfMessage
from sic_framework.core.component_python2 import SICComponent
from sic_framework.core.connector import SICConnector
from sic_framework.core.message_python2 import SICMessage, SICRequest
import openai

"""
Please use this version of openai, and not the recently updated version as this file has not been updated yet.
pip install openai==0.28.1
"""

class GPTConf(SICConfMessage):
    """
    GPT configuration message that contains the OpenAI key
    :param openai_key: your secret OpenAI key, see https://platform.openai.com/docs/quickstart
    :param model: OpenAI model to use, see https://platform.openai.com/docs/models
    :param temp: temperature parameter of the model; controls randomness, 0 means deterministic, 1 very random
    :param max_tokens: controls length of response by model
    """

    def __init__(self, openai_key, model="gpt-3.5-turbo-16k", temp=0.5, max_tokens=110):
        super(SICConfMessage, self).__init__()
        self.openai_key = openai_key
        self.model = model
        self.temperature = temp
        self.max_tokens = max_tokens


class GPTResponse(SICMessage):
    """
    The GPT response will be wrapped in this class.
    :param response: the actual response from the model
    :param num_tokens: TODO
    """
    def __init__(self, response, num_tokens):
        super().__init__()
        self.response = response
        self.num_tokens = num_tokens


class GPTRequest(SICRequest):
    """
    Main request for interacting with OpenAI GPT models.
    :param text: the text to send to the model

    For all other optional parameters, see GPTConf
    """
    def __init__(self, text, system_messages=None, context_messages=None, model=None, temp=None, max_tokens=None):
        super().__init__()
        self.text = text
        self.system_messages = system_messages
        self.context_messages = context_messages
        self.model = model
        self.temperature = temp
        self.max_tokens = max_tokens



class GPTComponent(SICComponent):
    """
    Dummy SICAction
    """

    def __init__(self, *args, **kwargs):
        super(GPTComponent, self).__init__(*args, **kwargs)
        openai.api_key = self.params.openai_key

    @staticmethod
    def get_inputs():
        return [GPTRequest]

    @staticmethod
    def get_output():
        return GPTResponse

    # This function is optional
    @staticmethod
    def get_conf():
        return GPTConf()

    # @backoff.on_exception(backoff.expo, openai.error.RateLimitError)
    def get_openai_response(self, user_messages, context_messages=None, system_messages=None, model=None, temp=None, max_tokens=None):
        """
        TODO
        """
        messages = []
        if system_messages:
            messages.append({"role": "system", "content": system_messages})
        if context_messages:
            for context_message in context_messages:
                messages.append({"role": "user", "content": context_message})

        messages.append({"role": "user", "content": user_messages})

        response = openai.ChatCompletion.create(
            model=model if model else self.params.model,
            messages=messages,
            temperature=temp if temp else self.params.temperature,
            max_tokens=max_tokens if max_tokens else self.params.max_tokens,
        )
        print(response)

        content = response.choices[0].message["content"]
        num_tokens = response['usage']['total_tokens']

        return GPTResponse(content, num_tokens)

    def on_message(self, message):
        pass
        # TODO
        # output = self.get_openai_response(message.text)
        # self.output_message(output)

    def on_request(self, request):
        print("GOT REQUEST", request)
        output = self.get_openai_response(request.text,
                                          system_messages=request.system_messages,
                                          context_messages=request.context_messages,
                                          model=request.model,
                                          temp=request.temperature,
                                          max_tokens=request.max_tokens)
        return output


class GPT(SICConnector):
    component_class = GPTComponent


if __name__ == '__main__':
    # Request the service to start using the SICServiceManager on this device
    SICComponentManager([GPTComponent])
