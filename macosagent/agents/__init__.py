from macosagent.agents.browser_agent import BrowserAgent
from macosagent.agents.calendar_agent import CalendarAgent
from macosagent.agents.player_agent import PlayerAgent
from macosagent.agents.preview_agent import PreviewAgent
from macosagent.agents.finder_agent import FinderAgent
from macosagent.agents.textedit_agent import TextEditAgent

agent_box = {
    "browser_agent": BrowserAgent(),
    "calendar_agent": CalendarAgent(),
    "preview_agent": PreviewAgent(),
    "player_agent": PlayerAgent(),
    "finder_agent": FinderAgent(),
    "textedit_agent": TextEditAgent(),
}

__all__ = ["agent_box"]
