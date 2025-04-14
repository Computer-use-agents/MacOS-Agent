from browser_agent import BrowserAgent
from calendar_agent import CalendarAgent
# from textedit_agent import TextEditAgent
from word_agent import WordAgent
# from finder_agent import FinderAgent
from powerpoint_agent import PowerPointAgent
from wechat_agent import WechatAgent
from excel_agent import ExcelAgent
from calendar_agent import CalendarAgent
from preview_agent import PreviewAgent

def get_app_agent_box():
    APP_AGENT_BOX = [
        # FinderAgent(),
        # TextEditAgent(),
        BrowserAgent(),
        PowerPointAgent(),
        WechatAgent(),
        WordAgent(),
        CalendarAgent(),
        ExcelAgent(),
        PreviewAgent(),
    ]
    return APP_AGENT_BOX
