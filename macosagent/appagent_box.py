"""Module containing the collection of application agents for the MacOS Agent system."""

from typing import List

from browser_agent import BrowserAgent
from calendar_agent import CalendarAgent
from excel_agent import ExcelAgent
from finder_agent import FinderAgent
from powerpoint_agent import PowerPointAgent
from preview_agent import PreviewAgent
from textedit_agent import TextEditAgent
from wechat_agent import WechatAgent
from word_agent import WordAgent


def get_app_agent_box() -> List[object]:
    """Get a list of all available application agents.
    
    Returns:
        List[object]: A list containing instances of all available application agents.
    """
    app_agent_box = [
        BrowserAgent(),
        CalendarAgent(),
        ExcelAgent(),
        FinderAgent(),
        PowerPointAgent(),
        PreviewAgent(),
        TextEditAgent(),
        WechatAgent(),
        WordAgent(),
    ]
    return app_agent_box
