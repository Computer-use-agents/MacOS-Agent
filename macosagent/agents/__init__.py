from macosagent.agents.browser_agent import BrowserAgent
from macosagent.agents.calendar_agent import CalendarAgent
from macosagent.agents.excel_agent import ExcelAgent
from macosagent.agents.finder_agent import FinderAgent
from macosagent.agents.player_agent import PlayerAgent
from macosagent.agents.powerpoint_agent import PowerPointAgent
from macosagent.agents.preview_agent import PreviewAgent
from macosagent.agents.textedit_agent import TextEditAgent
from macosagent.agents.wechat_agent import WechatAgent
from macosagent.agents.word_agent import WordAgent

agent_box = {
    "browser_agent": BrowserAgent(),
    "calendar_agent": CalendarAgent(),
    "preview_agent": PreviewAgent(),
    "player_agent": PlayerAgent(),
    "wechat_agent": WechatAgent(),
    "finder_agent": FinderAgent(),
    "textedit_agent": TextEditAgent(),
    "word_agent": WordAgent(),
    "excel_agent": ExcelAgent(),
    "powerpoint_agent": PowerPointAgent(),
}

__all__ = ["agent_box"]
