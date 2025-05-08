
from macosagent.agents.textedit_agent.textedit_agent.computeruse_tool.computer_use import ComputerControl
from macosagent.agents.textedit_agent.textedit_agent.computeruse_tool.summarize import Summarizer
from macosagent.agents.textedit_agent.textedit_agent.computeruse_tool.open import Open
from macosagent.agents.textedit_agent.textedit_agent.computeruse_tool.close import Close
from macosagent.agents.textedit_agent.textedit_agent.computeruse_tool.read_content import ReadContent

def get_visual_model_tool_box_for_computeruse():
    MODEL_TOOLBOX = [
        ComputerControl(),
        Open(),
        Close(),
        ReadContent(),
        Summarizer()
    ] 
    return MODEL_TOOLBOX