from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_openai.chat_models.base import BaseChatOpenAI
from omegaconf import DictConfig
from transformers.agents.llm_engine import HfEngine
from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage, SystemMessage
 
def create_gpt_4o(cfg: DictConfig) -> BaseChatOpenAI:
    REGION = cfg.region
    MODEL = cfg.model
    api_key = cfg.api_key
    API_BASE = cfg.api_base
    ENDPOINT = f"{API_BASE}/{REGION}"

    # Initialize the model
    llm = AzureChatOpenAI(
        model=MODEL,
        temperature=1.0,
        api_key=api_key,
        azure_endpoint=ENDPOINT,
        max_completion_tokens=256,
        api_version="2024-02-01",
    )
    return llm


class LLMEngine(HfEngine):
    def __init__(self, client: BaseChatOpenAI, model_id: str):
        self.client = client
        self.model_id = model_id

    def __call__(
        self, messages: List[Dict[str, str]], stop_sequences: Optional[List[str]] = None, grammar: Optional[str] = None
    ) -> str:
        input_messages = []
        for message in messages:
            if message["role"].value == "user":
                input_messages.append(HumanMessage(content=message["content"]))
            elif message["role"].value == "assistant":
                input_messages.append(AIMessage(content=message["content"]))
            elif message["role"].value == "tool-call":
                input_messages.append(ToolMessage(content=message["content"]))
            elif message["role"].value == "tool-response":
                input_messages.append(ToolMessage(content=message["content"]))
            elif message["role"].value == "system":
                input_messages.append(SystemMessage(content=message["content"]))
        return self.client.invoke(input_messages).content
