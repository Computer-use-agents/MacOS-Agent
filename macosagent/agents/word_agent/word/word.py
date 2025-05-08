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

from macosagent.agents.word_agent.word.utils import parse_axvalue_bounds
# from utils import parse_axvalue_bounds
logger = logging.getLogger(__name__)
@dataclass
class WordConfig:
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


def open_word(file_path=None):
	try:
		import os
		# abs_path = os.path.abspath(file_path)
		# os.system(f'open -a "Microsoft Word" "{abs_path}"')
		workspace = ApplicationServices.NSWorkspace.sharedWorkspace()
		
		workspace.launchApplication_("Microsoft Word")
		# print("open word")
		
		running_apps = workspace.runningApplications()
		# print(running_apps)
		# exit()
		word_app = None
		for app in running_apps:
			if app.localizedName() == "Microsoft Word":
				word_app = app
				word_app.activateWithOptions_(0)
				break
				
		if not word_app:
			raise Exception("Failed to get Microsoft.Word application")
		# print(file_path)
		# exit()
		# If there's a file path, use AppleScript to open the file
		if file_path:
			import os.path
			
			# exit()
			if not os.path.exists(file_path):
				from docx import Document
				doc = Document()
				doc.save(file_path)
				# raise FileNotFoundError(f"File not found: {file_path}")
			
			# Create AppleScript command
			abs_path = os.path.abspath(file_path)
			# print(abs_path)
			os.system(f'open -a "Microsoft Word" "{abs_path}"')
				
				# 使用AppleScript将Microsoft Word窗口置顶显示
			os.system('''
			osascript -e 'tell app "Microsoft Word" to activate'
			''')
			# exit()
			
			# Execute AppleScript
			
			time.sleep(1)  # Wait for file to open
			# print("finised")
			# exit()
		return word_app
	except Exception as e:
		# print(f"Error opening Word: {str(e)}")
		raise

# @singleton: TODO - think about id singleton makes sense here
# @dev By default this is a singleton, but you can create multiple instances if you need to.
class Word:
	"""
	Open Mac Word application and get the accessibility tree.
	"""

	def __init__(
		self,
		config: WordConfig = WordConfig(),
	):
		self.config = config
		# self.config.file_path = config.file_path
		self.powerpoint_app = None 
		# if config.file_path:
		# 	self.open_word(config.file_path)

	def open_word(self, file_path=None):
		self.config.file_path = file_path
		self.word_app = open_word(file_path)
		self.app_ref = ApplicationServices.AXUIElementCreateApplication(self.word_app.processIdentifier())
		time.sleep(1)  # Wait for window to open

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
					
		except Exception as e:
			print(f"处理元素时发生错误: {e}")
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
			return None
		finally:
			pass

	def get_app_windows(self):
		"""获取指定应用的窗口和accessibility tree"""
		try:
			# 获取窗口列表
			err, windows = ApplicationServices.AXUIElementCopyAttributeValue(
				self.app_ref, ApplicationServices.kAXWindowsAttribute, None
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
						print(f"获取accessibility tree时发生错误：{e}")
					
					# 查找对应的窗口ID并截图
					# print("window_list", window_list)
					for window_info in window_list:
						if window_info.get(Quartz.kCGWindowOwnerPID) == self.word_app.processIdentifier():
							window_id = window_info.get(Quartz.kCGWindowNumber)
							# print("Try get screenshot", window_id)
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
			print(f"发生错误：{e}")
			return None, None

if __name__ == "__main__":
	# pass
	word_app = Word(WordConfig(file_path = './data/test.pptx'))
	
	from typing import TYPE_CHECKING, Optional, TypedDict
	import argparse
	import json
	import os
	import sys
	import time
	import uuid
	import traceback
	import re
	from PIL import Image, ImageDraw, ImageFont
	import random
	from utils import BoxDrawer
 
	@dataclass	
	class WordContextState:
		"""
		State of the browser context
		"""

		accessibility_tree: list[dict] | None = None
		screenshots: list[Image.Image] | None = None
		screenshots_som: list[Image.Image] | None = None
		accessibility_tree_json: list[dict] | None = None
		offset: tuple[int, int] | None = None
	class WordContext:
		def __init__(
			self,
			word: 'Word',
			state: Optional[WordContextState] = None,
		):
			self.context_id = str(uuid.uuid4())
			logger.debug(f'Initializing new browser context with id: {self.context_id}')
			self.word = word
			self.state = state or WordContextState()


		def get_state(self):
			windows, screenshots = self.word.get_app_windows()
			self.state.accessibility_tree = windows
			self.state.screenshots = screenshots
			frame = parse_axvalue_bounds(windows[0]["attributes"]["AXFrame"])
			offset = (int(frame[0]), int(frame[1]))
			self.state.offset = offset
			# print(f"Offset: {offset}")
			# exit()
			w, h = frame[2], frame[3]
			background = screenshots[0].resize((int(w), int(h)))
			# print(self.state.accessibility_tree )
			# exit()
			# Create drawing object
			draw = ImageDraw.Draw(background)
			# Process the tree and draw bounding boxes
			som_drawer = BoxDrawer()
			boxes = som_drawer.process_tree(draw, windows, offset)
			background.save("output_image.png", "PNG")
			self.state.screenshots_som = [background]
			self.state.accessibility_tree_json = boxes
			return self.state
		
		def get_accessibility_tree_prompt(self):
			interactive_elements = self.state.accessibility_tree_json
			interactive_elements_prompt = ""
			for element in interactive_elements:
				if element is None:
					continue
				if "help" in element and len(element["help"]) > 0:
					interactive_elements_prompt += f"[{element['id']}]<{element['role']}>{element['desc']} ({element['help']})</{element['role']}>\n"
				else:
					interactive_elements_prompt += f"[{element['id']}]<{element['role']}>{element['desc']}</{element['role']}>\n"

			return interactive_elements_prompt, self.state.accessibility_tree_json


	word_context = WordContext(word_app)
	# print(word_context.get_state())