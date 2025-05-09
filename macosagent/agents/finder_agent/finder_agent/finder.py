from smolagents import Tool
from macosagent.agents.finder_agent.finder_agent.agents.finder import create_agent
from macosagent.llm.tracing import trace_with_metadata



class FinderAgent(Tool):
    name = 'finderagent'
    description = "A tool can solve GUI tasks about the Finder application in the Mac operating system."
    inputs = {
        "task": {"description": "instruction of a GUI task", "type": "string" }
    }
    output_type = "string"

    finder_agent = create_agent()

    @trace_with_metadata(observation_name="finder_agent", tags=["finder_agent"])
    def forward(self, task):
        return self.finder_agent.run(task)
