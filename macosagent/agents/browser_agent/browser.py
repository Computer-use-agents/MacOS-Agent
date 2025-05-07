import asyncio
import logging

from browser_use import Agent
from smolagents import Tool

from macosagent.llm import create_langchain_llm_client
from macosagent.llm.tracing import trace_with_metadata

logger = logging.getLogger(__name__)


class BrowserAgent(Tool):
    name = "browser_use"
    description = "A agent that can operate the browser to answer questions"
    inputs = {
        "instruction": {
            "description": "an instruction of a brower use agent",
            "type": "string",
        },
    }
    output_type = "string"

    llm = create_langchain_llm_client()
    @trace_with_metadata(observation_name="browser_agent", tags=["browser_agent"])
    def forward(self, instruction: str) -> str:
        logger.info(f"BrowserAgent instruction: {instruction}")
        agent = Agent(llm=self.llm, task=instruction)
        result = asyncio.run(agent.run(max_steps=30))
        logger.info(f"BrowserAgent result: {result.extracted_content}")
        return f"Execution result: {result.extracted_content}"
