import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field

import ApplicationServices
import Quartz
from PIL import Image
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowListOptionOnScreenOnly,
)

from macosagent.agents.calendar_agent.calendar.utils import parse_axvalue_bounds


def open_calendar(file_path=None):
    try:
        workspace = ApplicationServices.NSWorkspace.sharedWorkspace()
        # 先启动Preview应用
        workspace.launchApplication_("Calendar")

        # 从运行的应用中获取Preview应用对象
        running_apps = workspace.runningApplications()
        calendar_app = None
        for app in running_apps:
            # 使用bundleIdentifier来识别Preview应用
            if app.bundleIdentifier() == "com.apple.iCal":
                calendar_app = app
                calendar_app.activateWithOptions_(0)
                break

        if not calendar_app:
            raise Exception("Failed to get Calendar application")

        # 如果有文件路径，则打开文件
        if file_path:
            import os.path

            from Foundation import NSURL

            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_url = NSURL.fileURLWithPath_(file_path)
            success = workspace.openURL_(file_url)
            if not success:
                raise Exception(f"Failed to open file: {file_path}")

        return calendar_app
    except Exception:
        # print(f"Error opening Calendar: {str(e)}")
        raise


logger = logging.getLogger(__name__)
@dataclass
class CalendarConfig:
    r"""
    Configuration for the Browser.

    Default values:
        headless: True
            Whether to run browser in headless mode

        disable_security: True
            Disable browser security features

        extra_chromium_args: []
            Extra arguments to pass to the browser

        wss_url: None
            Connect to a browser instance via WebSocket

        cdp_url: None
            Connect to a browser instance via CDP

        chrome_instance_path: None
            Path to a Chrome instance to use to connect to your normal browser
            e.g. '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome'
    """

    process_id: str | None = None
    window_id: str | None = None
    window_id_list: list[str] = field(default_factory=list)
    save_screenshot_path: str | None = None
    use_som: bool = True


# @singleton: TODO - think about id singleton makes sense here
# @dev By default this is a singleton, but you can create multiple instances if you need to.
class Calendar:
    """
    Playwright browser on steroids.

    This is persistant browser factory that can spawn multiple browser contexts.
    It is recommended to use only one instance of Browser per your application (RAM usage will grow otherwise).
    """

    def __init__(
        self,
        config: CalendarConfig = CalendarConfig(),
    ):
        logger.debug('Initializing new browser')
        self.config = config

    def get_accessibility_tree(self, element, level=0, max_depth=10):
        """递归获取元素的accessibility tree，返回树形结构"""
        if level >= max_depth or not element:
            return None

        try:
            node = {
                'level': level,
                'children': [],
                'attributes': {}
            }

            # 获取元素的角色
            err, role = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXRoleAttribute, None
            )
            if err == 0:
                node['role'] = role

            # 获取标题
            err, title = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXTitleAttribute, None
            )
            if err == 0 and title:
                node['title'] = title

            # 检查是否可交互
            err, can_press = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXPressAction, None
            )
            err, can_focus = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXFocusedAttribute, None
            )

            node['is_interactive'] = (
                role in ['AXButton', 'AXLink', 'AXTextField', 'AXTextArea', 'AXCheckBox',
                        'AXRadioButton', 'AXComboBox', 'AXSlider', 'AXMenu', 'AXMenuItem',
                        'AXPopUpButton'] or
                can_press == True or
                can_focus == True
            )

            # 获取所有属性
            err, attributes = ApplicationServices.AXUIElementCopyAttributeNames(element, None)
            if err == 0:
                for attr in attributes:
                    if attr not in [ApplicationServices.kAXRoleAttribute, ApplicationServices.kAXTitleAttribute]:
                        err, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attr, None)
                        if err == 0:
                            node['attributes'][attr] = str(value)

            # 递归获取子元素
            err, children = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXChildrenAttribute, None
            )
            if err == 0 and children:
                for child in children:
                    child_node = self.get_accessibility_tree(child, level + 1, max_depth)
                    if child_node:
                        node['children'].append(child_node)

            return node

        except Exception:
            # print(f"处理元素时发生错误: {e}")
            return None

    def print_tree(self, node, indent=""):
        """打印树形结构"""
        if not node:
            return

        print(f"{indent}Role: {node.get('role', 'Unknown')}")
        if 'title' in node:
            print(f"{indent}Title: {node['title']}")
        if node['is_interactive']:
            print(f"{indent}Interactive: Yes")

        for attr, value in node['attributes'].items():
            print(f"{indent}{attr}: {value}")

        for child in node['children']:
            print(f"{indent}---")
            self.print_tree(child, indent + "  ")

    def capture_window_screenshot(self, frame_info):
        """捕获窗口截图"""
        temp_file = tempfile.mktemp('.png')
        temp_file_name = temp_file.split("/")[-1]
        temp_file = os.path.join("results", temp_file_name)
        # print("window_tree", window_tree[0])
        try:
            cmd = ['screencapture', '-o', '-x']
            cmd.append(f"-R{frame_info[0]},{frame_info[1]},{frame_info[2]},{frame_info[3]}")
            cmd.append(temp_file)
            # print("cmd", cmd)
            # 使用 screencapture 命令行工具捕获窗口
            subprocess.run(cmd, check=True)
            # 读取图片
            if os.path.exists(temp_file):
                return Image.open(temp_file)
            return None
        except Exception as e:
            # print(f"截图失败: {e}")
            logger.error(f"截图失败: {e}")
            return None
        finally:
            pass

    def get_app_windows(self):
        """获取指定应用的窗口和accessibility tree"""
        try:
            # 获取窗口列表
            err, windows = ApplicationServices.AXUIElementCopyAttributeValue(
                self.app, ApplicationServices.kAXWindowsAttribute, None
            )
            # print(windows, err)
            if err == 0 and windows:
                logger.info(f"\n找到 {len(windows)} 个窗口")
                window_trees = []  # 存储所有窗口的树形结构
                screenshots = []
                # 获取窗口信息
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                logger.info(f"window_list: {len(window_list)}")
                for i, window in enumerate(windows):
                    logger.info(f"\n窗口 {i + 1}:")
                    # print("=== Accessibility Tree ===")
                    try:
                        tree = self.get_accessibility_tree(window)
                        window_trees.append(tree)
                        # self.print_tree(tree)  # 打印树形结构
                    except Exception as e:
                        logger.error(f"获取accessibility tree时发生错误：{e}")

                    # 查找对应的窗口ID并截图
                    # print("window_list", window_list)
                    for window_info in window_list:
                        if window_info.get(Quartz.kCGWindowOwnerPID) == self.config.process_id:
                            window_id = window_info.get(Quartz.kCGWindowNumber)
                            logger.info(f"Try get screenshot, window_id: {window_id}")
                            if window_id not in self.config.window_id_list:
                                self.config.window_id_list.append(window_id)
                            # break # only get the first window
                    # pick the larger one to take screenshot
                    frame_infos = []
                    for window_tree in window_trees:
                        frame_info = parse_axvalue_bounds(window_tree["attributes"]["AXFrame"])
                        frame_infos.append(frame_info)
                    logger.info(f"frame_infos: {frame_infos}")
                    frame_info = max(frame_infos, key=lambda x: x[2] * x[3])
                    screenshot = self.capture_window_screenshot(frame_info)
                    screenshots.append(screenshot)

                return window_trees, screenshots  # 返回所有窗口的树形结构

        except Exception:
            logger.error(f"发生错误：{e}")
            return None

    def activate(self):
        if hasattr(self, "calendar_app"):
            self.calendar_app.activateWithOptions_(0)
            return

        target_app = open_calendar()
        pid = target_app.processIdentifier()
        app = ApplicationServices.AXUIElementCreateApplication(pid)
        self.config.process_id = pid
        self.app = app
        self.calendar_app = target_app

def log_granted_or_error(granted, error):
    if granted:
        logger.info("Calendar access granted")
    else:
        logger.error(f"Calendar access error: {error}")
if __name__ == "__main__":
    pass
