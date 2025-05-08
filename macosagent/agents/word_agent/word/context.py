"""
Playwright browser on steroids.
"""

import asyncio
import base64
import gc
import json
import logging
import os
import re
import time
import uuid
from PIL import Image
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, TypedDict

import argparse
import json
import os
import sys
import time
import traceback
import re
from PIL import Image, ImageDraw, ImageFont
import random

from macosagent.agents.word_agent.word.word import Word
from macosagent.agents.word_agent.word.utils import BoxDrawer, parse_axvalue_bounds
logger = logging.getLogger(__name__)



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
		
		# Create drawing object
		draw = ImageDraw.Draw(background)
		# Process the tree and draw bounding boxes
		som_drawer = BoxDrawer()
		boxes = som_drawer.process_tree(draw, windows, offset)
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


# if __name__ == "__main__":
   