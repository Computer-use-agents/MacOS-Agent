import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field

import ApplicationServices
import Quartz
from PIL import Image
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGNullWindowID,
    kCGWindowListOptionOnScreenOnly,
)

from macosagent.agents.preview_agent.preview.utils import parse_axvalue_bounds

logger = logging.getLogger(__name__)
@dataclass
class PreviewConfig:
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
    file_path: str | None = None


def open_preview(file_path=None):
    logger.info(f"Opening Preview with file path: {file_path}")
    try:
        workspace = ApplicationServices.NSWorkspace.sharedWorkspace()
        # First launch Preview application
        workspace.launchApplication_("Preview")

        # Get Preview app from running applications
        running_apps = workspace.runningApplications()
        preview_app = None
        for app in running_apps:
            if app.bundleIdentifier() == "com.apple.Preview":
                preview_app = app
                preview_app.activateWithOptions_(0)
                break

        if not preview_app:
            raise Exception("Failed to get Preview application")

        # If there's a file path, use AppleScript to open the file
        if file_path:
            import os.path

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Create AppleScript command
            abs_path = os.path.abspath(file_path)
            applescript = f'''tell application "Preview"
                activate
                open POSIX file "{abs_path}"
            end tell
            '''

            # Execute AppleScript
            subprocess.run(['osascript', '-e', applescript], check=True)
            time.sleep(1)  # Wait for file to open

        return preview_app
    except Exception as e:
        logger.error(f"Error opening Preview: {e!s}")
        raise

# @singleton: TODO - think about id singleton makes sense here
# @dev By default this is a singleton, but you can create multiple instances if you need to.
class Preview:
    """
    Open Mac Preview application and get the accessibility tree.
    """

    def __init__(
        self,
        config: PreviewConfig = PreviewConfig(),
    ):
        self.config = config
        if config.file_path:
            self.open_preview(config.file_path)

    def open_preview(self, file_path=None):
        self.config.file_path = file_path
        self.preview_app = open_preview(file_path)
        self.app_ref = ApplicationServices.AXUIElementCreateApplication(self.preview_app.processIdentifier())
        time.sleep(1)  # Wait for window to open

    def get_accessibility_tree(self, element, level=0, max_depth=10):
        if level >= max_depth or not element:
            return None

        try:
            node = {
                'level': level,
                'children': [],
                'attributes': {}
            }

            # Get role first to make early decisions
            err, role = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXRoleAttribute, None
            )
            if err == 0:
                node['role'] = role
                # Early return for sidebar elements we don't need
                if role in ["AXScrollArea"]:
                    return node  # Don't recurse into sidebar elements

            # Get title
            err, title = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXTitleAttribute, None
            )
            if err == 0 and title:
                node['title'] = title

            # Get attributes
            err, attributes = ApplicationServices.AXUIElementCopyAttributeNames(element, None)
            if err == 0:
                for attr in attributes:
                    if attr not in [ApplicationServices.kAXRoleAttribute, ApplicationServices.kAXTitleAttribute]:
                        err, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attr, None)
                        if err == 0:
                            node['attributes'][attr] = str(value)

            # Don't recurse into thumbnails or sidebar elements
            if role in ["AXImage", "AXScrollArea", "AXOutline", "AXList"]:
                return node

            # Get children only for main content
            err, children = ApplicationServices.AXUIElementCopyAttributeValue(
                element, ApplicationServices.kAXChildrenAttribute, None
            )
            if err == 0 and children:
                for child in children:
                    child_node = self.get_accessibility_tree(child, level + 1, max_depth)
                    if child_node:
                        node['children'].append(child_node)

            return node

        except Exception as e:
            logger.error(f"Error processing element: {e}")
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
            logger.info(f"cmd: {cmd}")
            # 使用 screencapture 命令行工具捕获窗口
            subprocess.run(cmd, check=True)
            # 读取图片
            if os.path.exists(temp_file):
                return Image.open(temp_file)
            return None
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
        finally:
            pass

    def get_app_windows(self):
        """获取指定应用的窗口和accessibility tree"""
        try:
            # 获取窗口列表
            logger.info("Getting app windows")
            err, windows = ApplicationServices.AXUIElementCopyAttributeValue(
                self.app_ref, ApplicationServices.kAXWindowsAttribute, None
            )
            logger.info(f"windows: {len(windows)}, err: {err}")
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
                        pass
                    except Exception as e:
                        logger.error(f"获取accessibility tree时发生错误：{e}")

                    # 查找对应的窗口ID并截图
                    # print("window_list", window_list)
                    for window_info in window_list:
                        if window_info.get(Quartz.kCGWindowOwnerPID) == self.preview_app.processIdentifier():
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

        except Exception as e:
            logger.error(f"发生错误：{e}")
            return None, None

if __name__ == "__main__":
    pass
