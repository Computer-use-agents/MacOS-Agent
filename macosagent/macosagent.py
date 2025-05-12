"""MacOS Agent module for creating and managing AI agents."""

from importlib.resources import files
from typing import Any

import yaml
from smolagents import CodeAgent

from macosagent.agents import agent_box
from macosagent.llm import create_smol_llm_client


def create_agent() -> CodeAgent:
    """Create and initialize a MacOS agent with configured model and tools.

    Returns:
        CodeAgent: An initialized MacOS agent instance with configured model and tools.
    """
    # Initialize the agent with the model and tools
    llm_engine = create_smol_llm_client()
    app_agent_box = []
    for _, v in agent_box.items():
        app_agent_box.append(v)
    with open(
        str(files("macosagent").joinpath("prompt.yaml")),
        encoding="utf-8") as file:
        prompt: dict[str, Any] = yaml.safe_load(file)

    macos_agent = CodeAgent(
        tools=app_agent_box,
        model=llm_engine,
        prompt_templates=prompt,
    )

    return macos_agent
