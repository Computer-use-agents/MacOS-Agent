from langchain_openai.chat_models.base import BaseChatOpenAI
from transformers.agents.llm_engine import HfEngine
from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage, SystemMessage
import os

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
