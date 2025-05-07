from macosagent.agents.browser_agent import BrowserAgent
from macosagent.agents.calendar_agent import CalendarAgent

agent_box = {
    "browser_agent": BrowserAgent(),
    "calendar_agent": CalendarAgent(),
}

__all__ = ["agent_box"]
