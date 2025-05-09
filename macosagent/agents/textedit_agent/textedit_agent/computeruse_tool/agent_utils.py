import ast
import base64
import logging
import math
import re
import backoff
import openai
import random


import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Dict, List
import numpy as np
from PIL import Image
from requests.exceptions import SSLError
from openai import OpenAI
from google.api_core.exceptions import (
    BadRequest,
    InternalServerError,
    InvalidArgument,
    ResourceExhausted,
)

    
def escape_single_quotes(text):
    # 匹配未转义的单引号（不匹配 \\'）
    pattern = r"(?<!\\)'"
    return re.sub(pattern, r"\\'", text)

def parsing_response_to_pyautogui_code(responses, input_swap:bool=True) -> str:
    '''
    将M模型的输出解析为OSWorld中的action，生成pyautogui代码字符串
    参数:
        response: 包含模型输出的字典，结构类似于：
        {
            "action_type": "hotkey",
            "action_inputs": {
                "hotkey": "command v",
                "start_box": None,
                "end_box": None
            }
        }
    返回:
        生成的pyautogui代码字符串
    '''

    pyautogui_code = f"import pyautogui\nimport time\n"
    if isinstance(responses, dict):
        responses = [responses]
    for response_id, response in enumerate(responses):
        if "observation" in response:
            observation = response["observation"]
        else:
            observation = ""

        if "thought" in response:
            thought = response["thought"]
        else:
            thought = ""

        action_dict = response
        action_type = action_dict.get("action_type")
        action_inputs = action_dict.get("action_inputs", {})
        
        if action_type == "HOT_KEY":
            # Parsing hotkey action
            hotkey = action_inputs.get("value", "").strip()
            if hotkey:
                # Handle other hotkeys
                keys = hotkey.split(" ")  # Split the keys by space
                pyautogui_code += f"\ntime.sleep(0.5)\n"
                pyautogui_code += f"\npyautogui.hotkey({', '.join([repr(k) for k in keys])}, interval=1)"
            else:
                pyautogui_code += f"\n# Unrecognized hot key action parsing: {action_type}"
                # logger.warning(f"Unrecognized hot key action parsing: {response}")
        elif action_type == "ENTER":
            pyautogui_code += f"\npyautogui.press('enter')"
        elif action_type == "INPUT":
            # Parsing typing action using clipboard
            content = action_inputs.get("value", "")
            content = escape_single_quotes(content)
            if content:
                if input_swap:
                    pyautogui_code += f"\nimport pyperclip"
                    pyautogui_code += f"\npyperclip.copy('{content.strip()}')"
                    pyautogui_code += f"\ntime.sleep(0.5)\n"
                    pyautogui_code += f"\npyautogui.hotkey('command', 'v', interval=1)"
                    pyautogui_code += f"\ntime.sleep(0.5)\n"
                    if content.endswith("\n") or content.endswith("\\n"):
                        pyautogui_code += f"\npyautogui.press('enter')"
                else:
                    pyautogui_code += f"\npyautogui.write('{content.strip()}', interval=0.1)"
                    pyautogui_code += f"\ntime.sleep(0.5)\n"
                    if content.endswith("\n") or content.endswith("\\n"):
                        pyautogui_code += f"\npyautogui.press('enter')"

        
        elif action_type in ["DRAG", "SELECT"]:
            # Parsing drag or select action based on start and end_boxes
            points = action_inputs.get("position")
            assert len(points) == 2 and len(points[0]) == 2 and len(points[1]) == 2, "Drag or select action should have 2 points"
            start_box = points[0]
            end_box = points[1]
            
            if start_box and end_box:
                x1, y1 = start_box # [x, y] float number between 0 and 1
                sx = round(float(x1), 3)
                sy = round(float(y1), 3)
                x2, y2 = end_box # [x, y] float number between 0 and 1
                ex = round(float(x2), 3)
                ey = round(float(y2), 3)
                pyautogui_code += (
                    f"\npyautogui.moveTo({sx}, {sy})\n"
                    f"\npyautogui.dragTo({ex}, {ey}, duration=1.0)\n"
                )
            # else:
            #     logger.warning(f"Parse failed! Drag or select action should have 2 points: {response}")
        elif action_type == "SCROLL":
            # Parsing scroll action
            start_box = action_inputs.get("position")
            if start_box:
                x, y = start_box
                x = round(float(x), 3)
                y = round(float(y), 3)                
                # # 先点对应区域，再滚动
                pyautogui_code += f"\npyautogui.click({x}, {y}, button='left')"
            else:
                x = None
                y = None
            direction = action_inputs.get("direction", "")
            
            if x == None:
                if "up" in direction.lower():
                    pyautogui_code += f"\npyautogui.scroll(5)"
                elif "down" in direction.lower():
                    pyautogui_code += f"\npyautogui.scroll(-5)"
            else:
                if "up" in direction.lower():
                    pyautogui_code += f"\npyautogui.scroll(5, x={x}, y={y})"
                elif "down" in direction.lower():
                    pyautogui_code += f"\npyautogui.scroll(-5, x={x}, y={y})"

        elif action_type in ["CLICK", "LEFT_CLICK_DOUBLE", "LEFT_CLICK_SINGLE", "RIGHT_CLICK_SINGLE", "HOVER"]:
            # Parsing mouse click actions
            start_box = action_inputs.get("position")
            # start_box = str(start_box)
            if start_box:
                # start_box = eval(start_box)
                if len(start_box) == 2:
                    x1, y1 = start_box
                    x2 = x1
                    y2 = y1
                else:
                    raise ValueError(f"Unknown start_box format: {start_box}")

                x = round(float((x1 + x2)/2), 3)
                y = round(float((y1 + y2)/2), 3)

                if action_type == "LEFT_CLICK_DOUBLE" or action_type == "CLICK":
                    pyautogui_code += f"\npyautogui.click({x}, {y}, button='left')"
                elif action_type == "LEFT_CLICK_DOUBLE":
                    pyautogui_code += f"\npyautogui.doubleClick({x}, {y}, button='left')"
                elif action_type == "RIGHT_CLICK_SINGLE":
                    pyautogui_code += f"\npyautogui.click({x}, {y}, button='right')"
                elif action_type == "HOVER":
                    pyautogui_code += f"\npyautogui.moveTo({x}, {y})"
        
        elif action_type in ["FINISH"]:
            pyautogui_code = f"DONE"
        
        else:
            pyautogui_code += f"\n# Unrecognized action type: {action_type}"
            # logger.error(f"Unrecognized action type: {response}")

    return pyautogui_code
