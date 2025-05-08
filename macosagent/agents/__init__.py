from macosagent.agents.browser_agent import BrowserAgent
from macosagent.agents.calendar_agent import CalendarAgent
from macosagent.agents.player_agent import PlayerAgent
from macosagent.agents.preview_agent import PreviewAgent
from macosagent.agents.word_agent import WordAgent
from macosagent.agents.excel_agent import ExcelAgent
from macosagent.agents.powerpoint_agent import PowerPointAgent

agent_box = {
    "browser_agent": BrowserAgent(),
    "calendar_agent": CalendarAgent(),
    "preview_agent": PreviewAgent(),
    "player_agent": PlayerAgent(),
    "word_agent": WordAgent(),
    "excel_agent": ExcelAgent(),
    "powerpoint_agent": PowerPointAgent(),
}

__all__ = ["agent_box"]
