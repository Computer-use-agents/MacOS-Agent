import base64
import json
import os

from openai import AzureOpenAI
from smolagents import Tool
from smolagents import AzureOpenAIServerModel
from smolagents import OpenAIServerModel
from dotenv import load_dotenv

from macosagent.agents.finder_agent.finder_agent.computeruse_tool.agent_utils import parsing_response_to_pyautogui_code 
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.get_accessibility_tree import GetTree
from macosagent.agents.finder_agent.finder_agent.computeruse_tool.draw_accessibility_tree import DrawTree
from macosagent.llm import create_smol_llm_client

# 加载 .env 文件
load_dotenv()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class ComputerControl(Tool):
    name = 'computer_control'
    description = "A tool that control the computer by performing mouse and keyboard operations."
    inputs = {
        "subgoal": {"description": "subgoal of a given task", "type": "string" }
    }
    output_type = "string"

    # if os.environ.get("API_SERVER_TYPE") == "AZURE":
    #     model = AzureOpenAIServerModel(
    #         model_id=os.environ.get("AZURE_MODEL"),
    #         azure_endpoint=os.environ.get("AZURE_ENDPOINT"),
    #         api_key=os.environ.get("AZURE_API_KEY"),
    #         api_version=os.environ.get("AZURE_API_VERSION"),
    #     )
    # elif os.environ.get("API_SERVER_TYPE") == "OPENAI":
    #     model = OpenAIServerModel(
    #         model_id=os.environ.get("MODEL"),
    #         api_base=os.environ.get("API_BASE"), 
    #         api_key=os.environ.get("API_KEY"),
    #     )
    # else:
    #     raise ValueError("Invalid API server type. Please check your .env file and ensure API_SERVER_TYPE is set to either 'AZURE' or 'OPENAI'.")

    model = create_smol_llm_client()

    SYSTEM_PROMPT = """You are an AI agent designed to automate GUI tasks. Your goal is to accomplish the task.
    You will be given a task instruction, interactive elements, the clean screenshot, and screenshot with highlighted elements.
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
    Thought: <Your reasoning process. You need to identify which element need to be interacted (recall its bounding box), and identify which action to interacta with the elements.>
    Element: <The element id that needs to be interacted.>
    Action: <The next action, it should be a JSON object, [{"action_type": <actions in the above provided action space>, “action_inputs”: {"value": <content to input or hot key or "N/A">, "direction": <'down' or 'up' or "N/A">,  "position": [x,y]}}]>

    You can output multiple actions at once, and use JSON array to represent multiple actions.
    If value or position is not applicable, set it as "N/A".
    Position might be [[x,y]] if the action requires only one position.
    Position might be [[x1,y1], [x2,y2]] if the action requires a start and end position (such as DRAG).
    In order to improve the success rate of interaction, the position should be in the middle of bounding box, not on the edge.
    NOTE that, this is the Mac operating system. The hot key for 'paste' is 'command v' instead of 'ctrl v'. The hot key for 'save' is 'command s' instead of 'ctrl s'. 

    """


    get_tree=GetTree()
    draw_tree=DrawTree()

    def forward(self, subgoal):
        try:
            [screenshot_path, accessibility_tree_path] = self.get_tree.forward('访达')
            [highlighted_screenshot_path, element_bbox_path] = self.draw_tree.forward('访达', screenshot_path, accessibility_tree_path)
        except:
            try:
                [screenshot_path, accessibility_tree_path] = self.get_tree.forward('Finder')
                [highlighted_screenshot_path, element_bbox_path] = self.draw_tree.forward('Finder', screenshot_path, accessibility_tree_path)
            except Exception as e:
                print(f"An error occurred: {e}")

        task = f"Task: f{subgoal}\nInteractive Elements:\n"
        with open(element_bbox_path, "r") as f:
            elements = json.load(f)
        for element in elements:
            if element is None:
                continue
            task += f"[{element['id']}]<{element['role']}>{element['desc']}</{element['role']}>. Bounding box in the screen ([x,y,w,h]): {element['bbox_screen']}.\n"


        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": task},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(highlighted_screenshot_path)}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(screenshot_path)}"}}
            ]},
        ]

        response = self.model(
            messages=messages,
            max_tokens=1024,
            temperature=1.0
        )
        content = response.content


        action = content.split("Action:")[1]

        try:
            action=json.loads(action)
            for act in action:
                pyautogui_code = parsing_response_to_pyautogui_code (act)
                exec(pyautogui_code)
            return "Some operations have performed on the computer, no explicit error."
        except:
            return "Some errors are occurred in performing operations on the computer.."

