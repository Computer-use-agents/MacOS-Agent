from typing import Optional

from macosagent.agents.finder_agent.finder_agent.computeruse_tool.computer_use import ComputerControl
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.summarize import Summarizer
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.open import Open
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.close import Close
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.copy import Copy
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.move import Move
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.delete import Delete
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.paste import Paste
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.rename import Rename
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.read_content import ReadContent

def get_visual_model_tool_box_for_computeruse():
    MODEL_TOOLBOX = [
        ComputerControl(),
        Open(),
        Close(),
        Copy(),
        Move(),
        Delete(),
        Paste(),
        Rename(),
        ReadContent(),
        Summarizer()
    ] 
    return MODEL_TOOLBOX