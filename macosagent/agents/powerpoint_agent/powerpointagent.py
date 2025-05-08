# from transformers import AutoProcessor, Tool
import os

from langchain_openai import AzureChatOpenAI
from smolagents import Tool

from .agent.service import ReactJsonAgent


class PowerPointAgent(Tool):
    name = "powerpoint_agent"
    description = "The PowerPoint-Agent is designed to perform a variety of tasks related to Microsoft PowerPoint presentations. It can handle basic operations such as opening, saving, and closing presentations, as well as more complex tasks like inserting images, tables, text, text boxes, and modifying styles (background color, text format). Additionally, it can delete content and interact with elements using PyAutoGUI. "
    inputs = {
        "instruction": {"description": "an instruction of a calendar app agent", "type": "string"},
    }
    output_type = "string"

    llm = AzureChatOpenAI(
        model = os.environ.get("AZURE_OPENAI_MODEL"),
        temperature=1.0,
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version=os.environ.get("OPENAI_API_VERSION"),
        max_completion_tokens=256,
    )

    agent = ReactJsonAgent(
        llm=llm,        
        max_iterations=10
    )
    
    def forward(self, instruction: str ) -> str:
        # result_example = "The to-do item 'Stefanie Sun's concert was on April 5, 2025.' has been added to your calendar. Task DONE."
        # return f"Execution result: {result_example}"
        result = self.agent.run(instruction)
        # print(result)
        return f"Execution result: {result}"
