import os

import dotenv

dotenv.load_dotenv()
from langfuse.decorators import observe
from langfuse.openai import AzureOpenAI, openai

openai.langfuse_auth_check()



@observe()
def story():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    )
    return client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
          {"role": "system", "content": "You are a great storyteller."},
          {"role": "user", "content": "How are you?"}
        ],
        max_completion_tokens=256,
        temperature=1.0,
    ).choices[0].message.content

@observe()
def multi_modal():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    )
    import base64
    with open("figure/acc_tree1.png", "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    return client.chat.completions.create(
        model=os.getenv("AZURE_MODEL"),
        messages=[
          {"role": "user", "content": [
              {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_data}"
                }
              },
              {
                "type": "text",
                "text": "What is in the image?"
              }
          ]}
        ],
        max_completion_tokens=256,
        temperature=1.0,
    ).choices[0].message.content

@observe()
def main():
    return story()


def test_case1():
    print(main())

def test_case2():
    print(multi_modal())
