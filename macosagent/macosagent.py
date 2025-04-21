"""MacOS Agent module for creating and managing AI agents."""

import os
import sys
from importlib.resources import files
from typing import Any

import yaml
from smolagents import AzureOpenAIServerModel, CodeAgent, OpenAIServerModel
from macosagent.appagent_box import get_app_agent_box

# Add current directory to Python path
sys.path.append('.')


def create_agent() -> CodeAgent:
    """Create and initialize a MacOS agent with configured model and tools.

    Returns:
        CodeAgent: An initialized MacOS agent instance with configured model and tools.
    """
    # Initialize the agent with the model and tools
    if os.environ.get("API_SERVER_TYPE") == "AZURE":
        llm_engine = AzureOpenAIServerModel(
            model_id=os.environ.get("AZURE_MODEL"),
            azure_endpoint=os.environ.get("AZURE_ENDPOINT"),
            api_key=os.environ.get("AZURE_API_KEY"),
            api_version=os.environ.get("AZURE_API_VERSION"),
        )
    elif os.environ.get("API_SERVER_TYPE") == "OPENAI":
        llm_engine = OpenAIServerModel(
            model_id=os.environ.get("MODEL"),
            api_base=os.environ.get("API_BASE"),
            api_key=os.environ.get("API_KEY"),
        )
    else:
        raise ValueError(
            "Invalid API server type. Please check your .env file and ensure "
            "API_SERVER_TYPE is set to either 'AZURE' or 'OPENAI'."
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
