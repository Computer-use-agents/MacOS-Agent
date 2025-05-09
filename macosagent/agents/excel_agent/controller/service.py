import asyncio
import base64
import json
import enum
import logging
from typing import Dict, Generic, Optional, Type, TypeVar
import icalendar
import os
import subprocess
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
import tempfile
from datetime import datetime, timedelta
# from lmnr.sdk.laminar import Laminar
from langchain_openai import AzureChatOpenAI, AzureOpenAI
from omegaconf import OmegaConf
from pydantic import BaseModel
import time 
from macosagent.agents.excel_agent.controller.registry.service import Registry
from macosagent.agents.excel_agent.excel.context import ExcelContext
from macosagent.agents.excel_agent.controller.views import ClickElementAction, InputTextAction, DoneAction, OpenExcelAction, SaveFileAction
from macosagent.agents.excel_agent.controller.views import * 
from macosagent.agents.excel_agent.controller.action_utils import *
from macosagent.agents.excel_agent.agent.views import ActionResult, ActionModel
import pyautogui
import re
import shutil

from macosagent.llm.llm import create_smol_llm_client

logger = logging.getLogger(__name__)
Context = TypeVar('Context')
class Controller(Generic[Context]):
	def __init__(
		self,
		exclude_actions: list[str] = [],
		output_model: Optional[Type[BaseModel]] = None,
	):
		self.registry = Registry[Context](exclude_actions)

		"""Register all default browser actions"""

		if output_model is not None:
			# Create a new model that extends the output model with success parameter
			class ExtendedOutputModel(BaseModel):  # type: ignore
				success: bool = True
				data: output_model

			@self.registry.action(
				'Complete task - with return text and if the task is finished (success=True) or not yet  completly finished (success=False), because last step is reached',
				param_model=ExtendedOutputModel,
			)
			async def done(params: ExtendedOutputModel):
				# Exclude success from the output JSON since it's an internal parameter
				output_dict = params.data.model_dump()

				# Enums are not serializable, convert to string
				for key, value in output_dict.items():
					if isinstance(value, enum.Enum):
						output_dict[key] = value.value
				def run_applescript(script):
					"""运行 AppleScript 并返回输出"""
					process = subprocess.run(
						["osascript", "-e", script],
						text=True,
						capture_output=True
					)
					if process.returncode == 0:
						print("AppleScript 执行成功：", process.stdout.strip())
					else:
						print("AppleScript 执行失败：", process.stderr.strip())

				save_and_close_script = """
					tell application "Microsoft Excel"
						-- 保存文档
						save active workbook
						-- 关闭文档
						close active workbook
					end tell
					"""
				# print("preprocessing: save and close the current excel")
				run_applescript(save_and_close_script)
				return ActionResult(is_done=True, success=params.success, extracted_content=json.dumps(output_dict))
		else:

			@self.registry.action(
				'Complete task - with return text and if the task is finished (success=True) or not yet  completly finished (success=False), because last step is reached',
				param_model=DoneAction,
			)
			async def done(params: DoneAction):
				return ActionResult(is_done=True, success=params.success, extracted_content=params.text)
			
		@self.registry.action(
			"Click element",
			param_model=ClickElementAction,
		)
		async def click_element(params: ClickElementAction, context: ExcelContext):
			index = params.index
			element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
			x, y, w, h = element[0]["bbox"]
			offset = context.state.offset
			x = int(x + offset[0] + w/2)
			y = int(y + offset[1] + h/2)
			logger.info(f"Clicking element {element[0]}")
			try:
				logger.info(f"clicking element at {x}, {y}")
    
				if element[0]['role'] in ['AXCell','AXMenuButton','AXScrollBar','AXButton', 'AXRadioButton','AXValueIndicator','AXCheckBox','AXComboBox']:
					pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
				elif element[0]['role'] in ['AXLayoutArea']:
					pyautogui.click(x=x, y=y, clicks=2, interval=0.1, button='left')
				else:
					pyautogui.click(x=x, y=y, clicks=2, interval=0.1, button='left')
				return ActionResult(is_done=False, success=True, extracted_content=f"🖱️  Clicked button with index {params.index}", include_in_memory=True)
			except Exception as e:
				logger.error(f"Error clicking element: {e}")
				return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)
			
		@self.registry.action(
			"Input text into the element",
			param_model=InputTextAction,
		)
		async def input_text(params: InputTextAction, context: ExcelContext):
			offset = context.state.offset
			x = int(params.insert_x_position + offset[0] )
			y = int(params.insert_y_position+ offset[1] )
			try:
				logger.info(f"Inputting text {params.text} ")
				pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
				pyautogui.write(escape_single_quotes(params.text), interval=0.1)
				# pyautogui.press('enter')
				return ActionResult(is_done=False, success=True, extracted_content= f'⌨️  Input {params.text} ', include_in_memory=True)
			except Exception as e:
				logger.error(f"Error inputting text: {e}")
				return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)
		
		@self.registry.action(
			"Open mac excel application with file path.",
			param_model=OpenExcelAction,
		)
		async def open_excel(params: OpenExcelAction, context: ExcelContext):
			context.excel.open_excel(params.file_path)
			return ActionResult(is_done=False, success=True, extracted_content=f"🔍  Opened excel {params.file_path}", include_in_memory=True)

		@self.registry.action(
			"Save current file opened by excel application into a path.",
			param_model=SaveFileAction,
		)
		async def save_file(params: SaveFileAction, context: ExcelContext):
			
			try:
				# subprocess.run(['osascript', '-e', apple_script], check=True)
				pyautogui.hotkey('command', 's')
				if context.excel.config.file_path!= params.file_path:
					shutil.copy(context.excel.config.file_path, params.file_path)
			except subprocess.CalledProcessError as e:
				logger.error(f"Error saving file: {e}")
				return ActionResult(is_done=False, success=False, extracted_content=str(e))

			return ActionResult(is_done=False, success=True, extracted_content=f"🖼️  Saved file to {params.file_path} Successfully!", include_in_memory=True)
		
		@self.registry.action(
			"Generate pyautogui codes to compelete a subgoal , this includes all possible actions. Use this one other actions failed to achieve the expected goals.",
			param_model=ComputerUseAction,
		)
		async def computer_use(params: ComputerUseAction,context:ExcelContext):
			# client = AzureChatOpenAI(
			# 		model = os.environ.get("AZURE_OPENAI_MODEL"),
			# 		temperature=1.0,
			# 		api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
			# 		azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
			# 		api_version=os.environ.get("OPENAI_API_VERSION"),
			# 		max_completion_tokens=256,
			# 	)
			client = create_smol_llm_client()
			SYSTEM_PROMPT = """You are an AI agent designed to automate GUI tasks. Your goal is to accomplish the task.
				You will be given a task instruction, interactive elements, the clean screenshot, and screenshot with highlighted elements. You are provided with screenshots of the app, not the entire desktop. The current offset of the app is x:""" +  f""" {context.state.offset[0]}, y: {context.state.offset[1]}.""" + """ Please take these offsets into account when generating positions.
				Please output the next action and wait for the next observation. 

				Here is the action space:
				1. `CLICK`: Click on an element, value is not applicable and the position [x,y] is required. 
				2. `INPUT`: Type a string into an element, value is a string to type and the position [x,y] is required. 
				3. `SCROLL`: Scroll the screen, value is the direction to scroll and the position is start position of the scroll operation.
				4. `LEFT_CLICK_DOUBLE`: Left click on an element twice, value is not applicable and the position [x,y] is required.
				5. `RIGHT_CLICK_SINGLE`: Right click on an element once, value is not applicable and the position [x,y] is required.
				6. `DRAG`: Drag the cursor to the specified position with the left button pressed. Value is not applicable and position [[x1,y1], [x2,y2]] is the start and end position of the drag operation.
				7. `HOT_KEY`: Press a hot key, value is the hot key and the position is not applicable.
				8. `WAIT`: Wait for 5 seconds, and take a screenshot to check for any changes. Value and position are not applicable.
				9. `FINISH`: Finish the task. Value and position are not applicable.

				# Input Format
				Task
				Interactive Elements
				[index]<type>text</type>
				- index: Numeric identifier for interaction
				- type: HTML element type (button, input, etc.)
				- text: Element description
				- bounding box: [x,y,w,h]. Coordinates of the upper left corner of the bounding box [x,y] and the length and height of the bounding box [w,h].
				Example:
				[33]<button>Submit Form</button>

				# Output Format
				Thought: <Your reasoning process. You need to identify which element need to be interacted (recall its bounding box), and identify which action to interact with the elements.>
				Element: <The element id that needs to be interacted.>
				Action: <The next action, it should be a JSON object, [{"action_type": <actions in the above provided action space>, “action_inputs”: {"value": <content to input or hot key or "N/A">, "direction": <'down' or 'up' or "N/A">,  "position": [x,y]}}]>
				You can output multiple actions at once, and use JSON array to represent multiple actions.
				If value or position is not applicable, set it as "N/A".
				Position might be [[x,y]] if the action requires only one position.
				Position might be [[x1,y1], [x2,y2]] if the action requires a start and end position (such as DRAG).
				In order to improve the success rate of interaction, the position should be in the middle of bounding box, not on the edge.
				NOTE that, this is the Mac operating system. The hot key for 'paste' is 'command v' instead of 'ctrl v'. The hot key for 'save' is 'command s' instead of 'ctrl s'. 
			"""
			def encode_image(image_path):
				with open(image_path, "rb") as image_file:
					return base64.b64encode(image_file.read()).decode("utf-8")
			try:
				context.state.screenshots[-1].save('./temp_screenshots.png')
				context.state.screenshots_som[-1].save('./temp_screenshots_som.png')
			except:
				return ActionResult(is_done=False, success=False, extracted_content=f"save image failed", include_in_memory=True)
			try:
				messages = [
				{"role": "system", "content": SYSTEM_PROMPT},
				{"role": "user", "content": [
					{"type": "text", "text": params.goal_description},
					{"type": "image_url",
					"image_url": 
						{"url": f"data:image/jpeg;base64,{encode_image('./temp_screenshots.png')}"}
					},
					{"type": "image_url",
					"image_url": 
						{"url": f"data:image/jpeg;base64,{encode_image('./temp_screenshots_som.png')}"}
					},
				]},
	
			]
			
				response = client.chat.completions.create(
					model=MODEL,
					messages=messages,
					max_tokens=256,
					temperature=1.0
					# response_format = "json"
				)
			except:
				return ActionResult(is_done=False, success=False, extracted_content=f"something wrong with response generation", include_in_memory=True)


			content = response.choices[0].message.content
			# print ('----content------', content)
			action = content.split("Action:")[1]
			# action.replace("None", "'None'")

			# print ('----action------', action)
			try:
				action=json.loads(action)
				for act in action:
					pyautogui_code = parsing_response_to_pyautogui_code(act)
					# print('1111python code1111 \n' + pyautogui_code)
					exec(pyautogui_code)
					# print ('one action is executed.')
			except:
				return ActionResult(is_done=False, success=False, extracted_content=f"Some errors are occurred in performing operations on the computer..", include_in_memory=True)
			
			return ActionResult(is_done=False, success=True, extracted_content=f"🖼️ Goal Achieved Successfully!", include_in_memory=True)

		@self.registry.action(
			"Save the current file opened by word and close the word",
			param_model=SaveAndCloseAction,
		)
		async def save_and_close(params: SaveAndCloseAction,context:ExcelContext):
			try:
				def run_applescript(script):
					"""运行 AppleScript 并返回输出"""
					process = subprocess.run(
						["osascript", "-e", script],
						text=True,
						capture_output=True
					)
					if process.returncode == 0:
						print("AppleScript 执行成功：", process.stdout.strip())
					else:
						print("AppleScript 执行失败：", process.stderr.strip())

				save_and_close_script = """
					tell application "Microsoft Excel"
						-- 保存文档
						save active workbook
						-- 关闭文档
						close active workbook
					end tell
					"""
				# print("preprocessing: save and close the current excel")
				run_applescript(save_and_close_script)
				time.sleep(1)
				if context.excel.config.file_path!= params.file_path:
					try:
						shutil.copy(context.excel.config.file_path, params.file_path) 
					except:
						return ActionResult(is_done=False, success=False, extracted_content=f"copy file error", include_in_memory=True)
			except:
				# print('failed')
				return ActionResult(is_done=False, success=False, extracted_content=f"save and close file failed", include_in_memory=True)
			return ActionResult(is_done=False, success=True, extracted_content=f"🖼️  Saved file to {params.file_path} Successfully!", include_in_memory=True)
		
		@self.registry.action(
			"insert text to a specific cell. before executing this action, one must first save and close the current file.",
			param_model=InsertCellTextAction,
		)
		async def insert_cell_text(params: InsertCellTextAction,context:ExcelContext):
			result = insert_text_to_cell_function(params.file_path,params.file_save_path,params.sheet_name,params.cell_address,params.insert_text,params.insert_pos)
			if result['success'] == True:
				return ActionResult(is_done=False, success=True, extracted_content=f"🖼️  Saved file to {params.file_save_path} Successfully add the text to the cell!", include_in_memory=True)
			else:
				return ActionResult(is_done=False, success=True, extracted_content=f"failed because, {result['error_message']}", include_in_memory=True)
   		
		@self.registry.action(
			"delete text of a specific cell. before executing this action, one must first save and close the current file.",
			param_model=DeleteCellTextAction,
		)
		async def delete_cell_text(params: DeleteCellTextAction,context:ExcelContext):
			result = delete_single_cell_text_function(params.file_path,params.file_save_path,params.sheet_name,params.cell_address)
			if result['success'] == True:
				return ActionResult(is_done=False, success=True, extracted_content=f"🖼️  Saved file to {params.file_save_path} Successfully add the text to the cell!", include_in_memory=True)
			else:
				return ActionResult(is_done=False, success=True, extracted_content=f"failed because, {result['error_message']}", include_in_memory=True)
   		
     
		@self.registry.action(
			"create a ppt file",
			param_model=CreateExcelAction,
		)
		async def create_worksheet(params: CreateExcelAction,context:ExcelContext):
			try:
				create_excel_function(params.file_path)
			except:
				return ActionResult(is_done=False, success=False, extracted_content=f"create file failed", include_in_memory=True)
			return ActionResult(is_done=False, success=True, extracted_content=f"🖼️  create file to {params.file_path} Successfully!", include_in_memory=True)
			
		
   
	async def act(
		self,
		action: ActionModel,
		excel_context: ExcelContext,
	) -> ActionResult:
		"""Execute an action"""

		try:
			for action_name, params in action.model_dump(exclude_unset=True).items():
				if params is not None:
					result = await self.registry.execute_action(
						action_name,
						params,
						excel_context=excel_context,
					)
					if isinstance(result, str):
						return ActionResult(extracted_content=result)
					elif isinstance(result, ActionResult):
						return result
					elif result is None:
						return ActionResult()
					else:
						raise ValueError(f'Invalid action result type: {type(result)} of {result}')
			return ActionResult()
		except Exception as e:
			raise e

def escape_single_quotes(text):
    # 匹配未转义的单引号（不匹配 \\'）
    pattern = r"(?<!\\)'"
    return re.sub(pattern, r"\\'", text)

