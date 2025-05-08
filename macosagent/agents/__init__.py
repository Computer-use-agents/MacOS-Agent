from macosagent.agents.browser_agent import BrowserAgent
from macosagent.agents.calendar_agent import CalendarAgent
from macosagent.agents.player_agent import PlayerAgent
from macosagent.agents.preview_agent import PreviewAgent
from macosagent.agents.word_agent import WordAgent

agent_box = {
    "browser_agent": BrowserAgent(),
    "calendar_agent": CalendarAgent(),
    "preview_agent": PreviewAgent(),
    "player_agent": PlayerAgent(),
    "word_agent": WordAgent(),
}

__all__ = ["agent_box"]
