"""MacOS Agent module for creating and managing AI agents."""

import os
from importlib.resources import files
from typing import Any

import yaml
from smolagents import AzureOpenAIServerModel, CodeAgent

from appagent_box import get_app_agent_box


def create_agent() -> CodeAgent:
    """Create and initialize a MacOS agent with configured model and tools.

    Returns:
        CodeAgent: An initialized MacOS agent instance with configured model and tools.
    """
    # Initialize the agent with the model and tools
    llm_engine = AzureOpenAIServerModel(
        model_id=os.environ.get("AZURE_OPENAI_MODEL"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("OPENAI_API_VERSION"),
    )

    app_agent_box = get_app_agent_box()
    with open(str(files("macosagent").joinpath("prompt.yaml")), encoding="utf-8") as file:
        prompt: dict[str, Any] = yaml.safe_load(file)

    macos_agent = CodeAgent(
        tools=app_agent_box,
        model=llm_engine,
        prompt_templates=prompt,
    )

    return macos_agent
