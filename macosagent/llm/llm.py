from __future__ import annotations

import logging
import os

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from smolagents import AzureOpenAIServerModel, OpenAIServerModel
from transformers.agents.llm_engine import HfEngine

from macosagent.llm.tracing import openai

logger = logging.getLogger(__name__)

class AzureOpenAIServerModelImpl(AzureOpenAIServerModel):
    """Azure OpenAI Server Model with Langfuse integration."""

    def create_client(self):
        return openai.AzureOpenAI(**self.client_kwargs)


class OpenAIServerModelImpl(OpenAIServerModel):
    """OpenAI Server Model with Langfuse integration."""

    def create_client(self):
        return openai.OpenAI(**self.client_kwargs)


def create_smol_llm_client() -> AzureOpenAIServerModel | OpenAIServerModel:
    """
    Create a Smol agent client for either OpenAI or Azure OpenAI.
    """
    if os.environ.get("API_SERVER_TYPE") == "AZURE":
        llm_engine = AzureOpenAIServerModelImpl(
            model_id=os.environ.get("AZURE_MODEL"),
            azure_endpoint=os.environ.get("AZURE_ENDPOINT"),
            api_key=os.environ.get("AZURE_API_KEY"),
            api_version=os.environ.get("AZURE_API_VERSION"),
        )
    elif os.environ.get("API_SERVER_TYPE") == "OPENAI":
        llm_engine = OpenAIServerModelImpl(
            model_id=os.environ.get("MODEL"),
            api_base=os.environ.get("API_BASE"),
            api_key=os.environ.get("API_KEY"),
        )
    else:
        raise ValueError(
            "Invalid API server type. Please check your .env file and ensure "
            "API_SERVER_TYPE is set to either 'AZURE' or 'OPENAI'."
        )
    return llm_engine


def create_langchain_llm_client() -> AzureChatOpenAI | ChatOpenAI:
    """
    Create a LangChain client for either OpenAI or Azure OpenAI.

    Returns:
        BaseChatOpenAI: A LangChain chat model instance

    Raises:
        ValueError: If provider is not supported or required parameters are missing
    """
    provider = os.environ.get("API_SERVER_TYPE")
    if provider.lower() == "azure":
        endpoint = os.environ.get("AZURE_ENDPOINT")
        model = os.environ.get("AZURE_MODEL")
        if not endpoint:
            raise ValueError("Azure endpoint is required")
        return AzureChatOpenAI(
            model=model,
            temperature=1.0,
            api_key=os.getenv("AZURE_API_KEY"),
            azure_endpoint=endpoint,
            max_completion_tokens=256,
            api_version="2024-02-01",
        )
    elif provider.lower() == "openai":
        endpoint = os.environ.get("OPENAI_ENDPOINT")
        model = os.environ.get("OPENAI_MODEL")
        return ChatOpenAI(
            model=model,
            temperature=1.0,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=endpoint if endpoint else None,
        )
    else:
        raise ValueError(f"Provider {provider} not supported. Use 'openai' or 'azure'")


class LLMEngine(HfEngine):
    def __init__(self, client: AzureChatOpenAI | ChatOpenAI, model_id: str):
        self.client = client
        self.model_id = model_id

    def __call__(
        self,
        messages: list[dict[str, str]],
        stop_sequences: list[str] | None = None,
        grammar: str | None = None,
    ) -> str:
        input_messages = []
        for message in messages:
            if message["role"].value == "user":
                input_messages.append(HumanMessage(content=message["content"]))
            elif message["role"].value == "assistant":
                input_messages.append(AIMessage(content=message["content"]))
            elif message["role"].value == "tool-call" or message["role"].value == "tool-response":
                input_messages.append(ToolMessage(content=message["content"]))
            elif message["role"].value == "system":
                input_messages.append(SystemMessage(content=message["content"]))
        return self.client.invoke(input_messages).content
