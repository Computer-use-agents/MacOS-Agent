import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_openai.chat_models.base import BaseChatOpenAI
from omegaconf import DictConfig
from transformers.agents.llm_engine import HfEngine


def create_llm(cfg: DictConfig) -> BaseChatOpenAI:
    print(cfg)
    if cfg.provider == "azure":
        return create_azure_model(cfg.azure)
    elif cfg.provider == "openai":
        return create_openai_model(cfg.openai)
    elif cfg.provider == "anthropic":
        return create_anthropic_model(cfg.anthropic)
    elif cfg.provider == "qwen":
        return create_qwen_model(cfg.qwen)
    else:
        raise ValueError(f"Model {cfg.model} not supported")

def create_azure_model(cfg: DictConfig) -> BaseChatOpenAI:
    model = cfg.model
    endpoint = cfg.endpoint
    print("create_azure_gpt", model, endpoint)
    # Initialize the model
    llm = AzureChatOpenAI(
        model=model,
        temperature=1.0,
        api_key=os.getenv("AZURE_API_KEY"),
        azure_endpoint=endpoint,
        max_completion_tokens=256,
        api_version="2024-02-01",
    )
    return llm

def create_openai_model(cfg: DictConfig) -> BaseChatOpenAI:
    print("create_openai_gpt", cfg.model, cfg.endpoint)
    return ChatOpenAI(
        model=cfg.model,
        temperature=1.0,
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=cfg.endpoint
    )

def create_anthropic_model(cfg: DictConfig) -> BaseChatOpenAI:
    return ChatAnthropic(
        model=cfg.model,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_api_url=cfg.endpoint,
        temperature=1.0
    )

def create_qwen_model(cfg: DictConfig) -> BaseChatOpenAI:
    return create_qwen_model_with_params(cfg.model, cfg.endpoint)

def create_qwen_model_with_params(model: str, base_url: str) -> BaseChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=base_url,
        temperature=1.0
    )

class LLMEngine(HfEngine):
    def __init__(self, client: BaseChatOpenAI, model_id: str):
        self.client = client
        self.model_id = model_id

    def __call__(
        self, messages: list[dict[str, str]], stop_sequences: list[str] | None = None, grammar: str | None = None
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
