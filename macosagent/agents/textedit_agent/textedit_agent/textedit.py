from smolagents import Tool
from macosagent.agents.textedit_agent.textedit_agent.agents.textedit_use import create_agent
from macosagent.llm.tracing import trace_with_metadata

class TextEditAgent(Tool):
    name = 'texteditagent'
    description = "A tool can solve GUI tasks about the TextEdit application in the Mac operating system."
    inputs = {
        "task": {"description": "instruction of a GUI task", "type": "string" }
    }
    output_type = "string"

    textedit_agent = create_agent()

    @trace_with_metadata(observation_name="textedit_agent", tags=["textedit_agent"])
    def forward(self, task):
        return self.textedit_agent.run(task)
