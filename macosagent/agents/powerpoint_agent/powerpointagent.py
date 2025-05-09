import asyncio
import base64
import json
import logging
import os
import time
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional
from langchain_core.messages import BaseMessage

from langchain_openai import AzureChatOpenAI
from smolagents import Tool


from macosagent.llm import create_langchain_llm_client
from macosagent.llm.tracing import trace_with_metadata

from macosagent.agents.powerpoint_agent.agent.prompt import SYSTEM_PROMPT
from macosagent.agents.powerpoint_agent.agent.views import (
    ActionModel,
    ActionResult,
    AgentOutput,
)

from macosagent.agents.powerpoint_agent.agent.service import ReactJsonAgent

logger = logging.getLogger(__name__)


def log_response(response: AgentOutput) -> None:
    """Utility function to log the model's response."""

    if "Success" in response.current_state.evaluation_previous_goal:
        emoji = "👍"
    elif "Failed" in response.current_state.evaluation_previous_goal:
        emoji = "⚠"
    else:
        emoji = "🤷"

    logger.info(f"{emoji} Eval: {response.current_state.evaluation_previous_goal}")
    logger.info(f"🧠 Memory: {response.current_state.memory}")
    logger.info(f"🎯 Next goal: {response.current_state.next_goal}")
    for i, action in enumerate(response.action):
        logger.info(
            f"🛠️  Action {i + 1}/{len(response.action)}: {action.model_dump_json(exclude_unset=True)}"
        )

def _write_messages_to_file(f: Any, messages: list[BaseMessage]) -> None:
    """Write messages to conversation file"""
    for message in messages:
        f.write(f" {message.__class__.__name__} \n")

        if isinstance(message.content, list):
            for item in message.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    f.write(item["text"].strip() + "\n")
        elif isinstance(message.content, str):
            if len(message.content) > 0:
                try:
                    content = json.loads(message.content)
                    f.write(json.dumps(content, indent=2) + "\n")
                except json.JSONDecodeError:
                    f.write(message.content.strip() + "\n")
            if (
                hasattr(message, "tool_calls")
                and message.tool_calls is not None
                and len(message.tool_calls) > 0
            ):
                tool_calls = message.tool_calls
                f.write(json.dumps(tool_calls, indent=2) + "\n")
            if (
                hasattr(message, "tool_call_id")
                and message.tool_call_id is not None
                and len(message.tool_call_id) > 0
            ):
                f.write(f"Tool call id: {message.tool_call_id}\n")

        f.write("\n")



class PowerPointAgent(Tool):
    name = "powerpoint_agent"
    description = "The PowerPoint-Agent is designed to perform a variety of tasks related to Microsoft PowerPoint presentations. It can handle basic operations such as opening, saving, and closing presentations, as well as more complex tasks like inserting images, tables, text, text boxes, and modifying styles (background color, text format). Additionally, it can delete content and interact with elements using PyAutoGUI. "
    inputs = {
        "instruction": {"description": "an instruction of a calendar app agent", "type": "string"},
    }
    output_type = "string"

    
    @trace_with_metadata(observation_name="powerpoint_agent", tags=["powerpoint_agent"])
    def forward(self, instruction: str ) -> str:
        logger.info(f"PowerPointAgent instruction: {instruction}")
        llm = create_langchain_llm_client()
        agent = ReactJsonAgent(
            llm=llm,
            max_iterations=20
        )
        result = agent.run(instruction)
        return result
       