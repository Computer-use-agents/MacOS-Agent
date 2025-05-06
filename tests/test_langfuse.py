import os

import dotenv
import pytest
from langfuse.decorators import observe
from langfuse import Langfuse
from langfuse.openai import openai # OpenAI integration
from langfuse.openai import OpenAI, AzureOpenAI

dotenv.load_dotenv()

@pytest.fixture
def test_langfuse():
    langfuse = langfuse.Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

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
          {"role": "user", "content": "Once upon a time in a galaxy far, far away..."}
        ],
    ).choices[0].message.content

@observe()
def main():
    return story()


def test_langfuse_observe():
    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

    main()