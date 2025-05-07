import logging
from dataclasses import dataclass, field
import ApplicationServices
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
import Quartz
import numpy as np
from PIL import Image
import time
import subprocess
import tempfile
import json
import ctypes
import os

from macosagent.agents.wechat_agent.wechat.utils import parse_axvalue_bounds

logger = logging.getLogger(__name__)
@dataclass
class WechatConfig:
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
	app_name: str | None = None
	save_screenshot_path: str | None = None
	use_som: bool = True

def open_wechat(app_name):
	workspace = ApplicationServices.NSWorkspace.sharedWorkspace()
	
	# workspace.launchApplication_(app_name)
	
	# os.system(f'open -a "{app_name}"')
	
	running_apps = workspace.runningApplications()
	wechat_app = None
	for app in running_apps:
		try:
			if app.localizedName() == app_name:
				wechat_app = app
				# wechat_app.activateWithOptions_(0)
				break
		except:
			if app.localizedName() == "WeChat":
				wechat_app = app
				# wechat_app.activateWithOptions_(0)
				break	
	
	if not wechat_app:
		raise Exception("Failed to get Wechat application")
		
	return wechat_app

# @singleton: TODO - think about if singleton makes sense here
# @dev By default this is a singleton, but you can create multiple instances if you need to.
class Wechat:
	"""
	Playwright browser on steroids.

	This is a persistent browser factory that can spawn multiple browser contexts.
	It is recommended to use only one instance of Browser per your application (RAM usage will grow otherwise).
	"""

	def __init__(
		self,
		config: WechatConfig = WechatConfig(),
	):
		logger.debug('Initializing new browser')
		self.config = config
		app_name = self.config.app_name
		
		try:
			wechat_app = open_wechat(app_name)
		except:
			try:
				wechat_app = open_wechat("WeChat")
			except:
				wechat_app = open_wechat("微信")

		if not wechat_app:
			# print(f"Could not find application: {app_name}")
			return

        # 获取应用进程信息
		pid = wechat_app.processIdentifier()
		app = ApplicationServices.AXUIElementCreateApplication(pid)
		self.config.process_id = pid
		self.app = app
		self.app_name = app_name
		self.wechat_app = wechat_app

	def get_accessibility_tree(self, element, level=0, max_depth=10):
		if level >= max_depth or not element:
			return None
			
		try:
			node = {
				'level': level,
				'children': [],
				'attributes': {}
			}
			
			err, role = ApplicationServices.AXUIElementCopyAttributeValue(
				element, ApplicationServices.kAXRoleAttribute, None
			)
			if err == 0:
				node['role'] = role
			
			err, title = ApplicationServices.AXUIElementCopyAttributeValue(
				element, ApplicationServices.kAXTitleAttribute, None
			)
			if err == 0 and title:
				node['title'] = title
				
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
				can_press or 
				can_focus
			)
			
			err, attributes = ApplicationServices.AXUIElementCopyAttributeNames(element, None)
			if err == 0:
				for attr in attributes:
					if attr not in [ApplicationServices.kAXRoleAttribute, ApplicationServices.kAXTitleAttribute]:
						err, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attr, None)
						if err == 0:
							node['attributes'][attr] = str(value)
			
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
			# print(f"Error occurred while processing element: {e}")
			return None

	def print_tree(self, node, indent=""):
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
		temp_file = tempfile.mktemp('.png')
		temp_file_name = temp_file.split("/")[-1]
		temp_file = os.path.join("results", temp_file_name)
		# print("window_tree", window_tree[0])
		try:
			cmd = ['screencapture', '-o', '-x']
			cmd.append(f"-R{frame_info[0]},{frame_info[1]},{frame_info[2]},{frame_info[3]}")
			cmd.append(temp_file)
			# print("cmd", cmd)
			subprocess.run(cmd, check=True)

			if os.path.exists(temp_file):
				return Image.open(temp_file)
			return None
		except Exception as e:
			# print(f"Screenshot failed: {e}")
			return None
		finally:
			pass

	def get_app_windows(self):
		try:
			# os.system(f'''
			# 	osascript -e 'tell app "{self.app_name}" to activate'
			# ''')

			self.wechat_app.activateWithOptions_(0)

			err, windows = ApplicationServices.AXUIElementCopyAttributeValue(
				self.app, ApplicationServices.kAXWindowsAttribute, None
			)
			# print(windows, err)
			if err == 0 and windows:
				logger.info(f"\nFound {len(windows)} windows")
				window_trees = []
				screenshots = []

				window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
				logger.info(f"window_list: {len(window_list)}")
				for i, window in enumerate(windows):
					logger.info(f"\nWindow {i + 1}:")
					
					# print("=== Accessibility Tree ===")
					
					tree = self.get_accessibility_tree(window)
					window_trees.append(tree)
					# # self.print_tree(tree)
					# with open (os.path.join("results", f"window_tree_{i}.json"), "w") as f:
					# 	json.dump(tree, f, indent=4)
					# 	logger.info(f"Accessibility tree for window {i + 1} saved to results/window_tree_{i}.json")
					
					# print("window_list", window_list)
					for window_info in window_list:
						if window_info.get(Quartz.kCGWindowOwnerPID) == self.config.process_id:
							window_id = window_info.get(Quartz.kCGWindowNumber)
							# print("Trying to get screenshot", window_id)
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
					
				return window_trees, screenshots
			
		except Exception as e:
			# print(f"Error occurred: {e}")
			return None, None

if __name__ == "__main__":
	pass