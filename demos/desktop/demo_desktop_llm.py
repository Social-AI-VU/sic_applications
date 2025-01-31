from sic_framework.services.llm.llm_component import (
    LlmConf,
    LlmResponse,
    PromptRequest,
    SICLlm,
)


def test_llm():
    # Initialize the LLM component with your configuration
    llmconf = LlmConf(
        model="orca-mini-3b-gguf2-q4_0",
        system_prompt="You are a helpful assistant",
    )

    # If you want to use an OpenAI model
    # Generate your personal openai api key here: https://platform.openai.com/api-keys
    # Either add your openai key to your systems variables (and comment the next line out) or
    # create a .openai_env file in the conf/openai folder and add your key there like this:
    # OPENAI_API_KEY="your key"

    # from dotenv import load_dotenv
    # from os.path import abspath, join
    # from os import environ

    # load_dotenv(abspath(join("..", "..", "conf", "openai", ".openai_env")))

    # llmconf = LlmConf(
    #     model="gpt-4o-mini",
    #     openai_key=environ["OPENAI_API_KEY"],
    #     system_prompt="You are a helpful assistant",
    # )

    llm_component = SICLlm(conf=llmconf)

    # Test with a simple prompt
    prompt = "What is the capital of France? Please answer in one word."
    request = PromptRequest(prompt)

    try:
        # Send the request and get the response
        response = llm_component.request(request)
        print(f"Prompt: {prompt}")
        print(f"Response: {response.response}")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up
        llm_component.stop()


if __name__ == "__main__":
    test_llm()
