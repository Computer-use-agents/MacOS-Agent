import base64
import enum
import json
import logging
import re
import time
from typing import Generic, TypeVar

import pyautogui
import Quartz
from moviepy.editor import VideoFileClip
from openai import OpenAI
from pydantic import BaseModel

from macosagent.agents.player_agent.agent.views import ActionModel, ActionResult
from macosagent.agents.player_agent.controller.registry.service import Registry
from macosagent.agents.player_agent.controller.views import (
    ClickElementAction,
    DoneAction,
    DragAction,
    ExtractVideoEventsAction,
    InputTextAction,
    OpenQuickTimePlayerAction,
    PressHotKeyAction,
)
from macosagent.agents.player_agent.player.context import PlayerContext

logger = logging.getLogger(__name__)
Context = TypeVar('Context')
class Controller(Generic[Context]):
    def __init__(
        self,
        exclude_actions: list[str] = [],
        output_model: type[BaseModel] | None = None,
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
        async def click_element(params: ClickElementAction, context: PlayerContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            logger.info(f"Clicking element {element[0]}")
            try:
                logger.info(f"clicking element at {x}, {y}")
                if element[0]["role"] == "AXList":
                    pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='right')
                elif element[0]["role"] == "AXButton" or element[0]["role"] == "AXRadioButton":
                    pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
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
        async def input_text(params: InputTextAction, context: PlayerContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            try:
                logger.info(f"Inputting text {params.text} into element {element[0]}")
                pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                # clear the text
                keys = normalize_keys(['CMD', 'A'])
                simulate_key_combination(keys)
                keys = normalize_keys(['DELETE'])
                simulate_key_combination(keys)
                pyautogui.write(escape_single_quotes(params.text), interval=0.1)
                pyautogui.press('enter')
                return ActionResult(is_done=False, success=True, extracted_content= f'⌨️  Input {params.text} into index {params.index}', include_in_memory=True)
            except Exception as e:
                logger.error(f"Error inputting text: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Open QuickTime player with file path.",
            param_model=OpenQuickTimePlayerAction,
        )
        async def open_quicktime_player(params: OpenQuickTimePlayerAction, context: PlayerContext):
            metadata = None
            if params.file_path is not None and params.file_path.endswith(".mp4"):
                metadata = get_video_metadata(params.file_path)

            context.player.open_player(params.file_path)
            extract_content = f"🔍  Opened quicktime player with {params.file_path} successfully!"
            if metadata is not None:
                extract_content += "\n"
                extract_content += f"Video metadata: {json.dumps(metadata, indent=2)}"
            return ActionResult(is_done=False, success=True, extracted_content=extract_content, include_in_memory=True)

        @self.registry.action(
            "Press hot key combination. Key are separated by space",
            param_model=PressHotKeyAction,
        )
        async def press_hot_key(params: PressHotKeyAction, context: PlayerContext):
            logger.info(f"Pressing hot key combination: {params.keys}")
            keys = params.keys.split(" ")
            normlized_keys = normalize_keys(keys)
            logger.info(f"Normlized keys: {normlized_keys}")
            simulate_key_combination(normlized_keys)
            return ActionResult(is_done=False, success=True, extracted_content=f"🔑  Pressed hot key combination: {params.keys} successfully!", include_in_memory=True)

        @self.registry.action(
            "Drag element from source index to target index with a distance. Distance is a float number between 0-1 which indicates the relative distance between the source and target index",
            param_model=DragAction,
        )
        async def drag_element(params: DragAction, context: PlayerContext):
            start_element = [item for item in context.state.accessibility_tree_json if item["id"] == params.source_index]
            end_element = [item for item in context.state.accessibility_tree_json if item["id"] == params.target_index]
            logger.info(f"Dragging element from {start_element[0]} to {end_element[0]} with a distance of {params.distance}")
            x1, y1, w1, h1 = start_element[0]["bbox"]
            x2, y2, w2, h2 = end_element[0]["bbox"]
            offset = context.state.offset
            x1 = int(x1 + offset[0] + w1/2)
            y1 = int(y1 + offset[1] + h1/2)
            x2 = int(x2 + offset[0] + w2/2)
            y2 = int(y2 + offset[1] + h2/2)
            dx, dy = (x2 - x1) * params.distance, (y2 - y1) * params.distance
            x_end, y_end = x1 + dx, y1 + dy
            logger.info(f"Dragging from {x1}, {y1} to {x_end}, {y_end} with a distance of {params.distance}")
            pyautogui.moveTo(x1, y1)
            pyautogui.dragTo(x_end, y_end, duration=1.0, button='left')
            return ActionResult(is_done=False, success=True, extracted_content=f"🔄  Dragged element from {params.source_index} to {params.target_index} with a distance of {params.distance} successfully!", include_in_memory=True)

        @self.registry.action(
            "Extract video content. It returns a list of events with start time, end time and event description. Good for trim part of the video.",
            param_model=ExtractVideoEventsAction,
        )
        async def extract_video_events(params: ExtractVideoEventsAction, context: PlayerContext):


            # Encode video to base64
            def encode_video(video_path):
                with open(video_path, "rb") as video_file:
                    return base64.b64encode(video_file.read()).decode("utf-8")

            # Get video path from context
            video_path = context.player.current_video_path
            if not video_path:
                return ActionResult(is_done=False, success=False, extracted_content="No video file is currently open", include_in_memory=True)

            base64_video = encode_video(video_path)

            # Initialize OpenAI client with DashScope
            client = OpenAI(
                api_key=os.getenv('DASHSCOPE_API_KEY'),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

            try:
                completion = client.chat.completions.create(
                    model="qwen-vl-max-latest",
                    messages=[
                        {
                            "role": "system",
                            "content": [{"type":"text","text": "You are a helpful assistant."}]
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "video_url",
                                    "video_url": {"url": f"data:video/mp4;base64,{base64_video}"},
                                    "fps": 2.0
                                },
                                {"type": "text", "text": "Please describe the series of events in the video, output in JSON format with start_time, end_time, and event description."},
                            ],
                        }
                    ],
                )

                # Parse the response and return as ActionResult
                events = json.loads(completion.choices[0].message.content)
                return ActionResult(
                    is_done=False,
                    success=True,
                    extracted_content=json.dumps(events, indent=2, ensure_ascii=False),
                    include_in_memory=True
                )
            except Exception as e:
                logger.error(f"Error extracting video events: {e}")
                return ActionResult(
                    is_done=False,
                    success=False,
                    extracted_content=str(e),
                    include_in_memory=True
                )
    async def act(
        self,
        action: ActionModel,
        player_context: PlayerContext,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    result = await self.registry.execute_action(
                        action_name,
                        params,
                        player_context=player_context,
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


def get_video_metadata(file_path):
    try:
        clip = VideoFileClip(file_path)
        metadata = {
            'duration': clip.duration,          # 持续时间（秒）
            'width': clip.w,                    # 宽度
            'height': clip.h,                   # 高度
            'fps': clip.fps,                    # 帧率
            'size': clip.size,                  # (width, height)
            'rotation': clip.rotation           # 旋转角度
        }
        clip.close()
        return metadata
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return None


def normalize_keys(keys: list[str]) -> list[int]:
    """
    Normalize keys to key codes
    """
    normlized_keys = []
    for k in keys:
        k = k.upper()
        if k == "COMMAND":
            k = "CMD"
        elif k == "OPTION":
            k = "OPT"
        if k not in KEY_CODES:
            raise ValueError(f"Key {k} not found in KEY_CODES, Unk Key Error!!")
        normlized_keys.append(KEY_CODES[k])
    return normlized_keys


def simulate_key_combination(keys):
    """
    Simulate pressing multiple keys simultaneously
    
    Args:
        keys: List of key codes to press. Example: [0x37, 0x3A, 0x2D] for CMD+OPT+N
    """
    # Common key codes for reference
    KEY_CODES = {
        'CMD': 0x37,
        'OPT': 0x3A,
        'SHIFT': 0x38,
        'CTRL': 0x3B,
        'N': 0x2D,
        'O': 0x1F,
        'ESC': 0x35,
        # Add more as needed
    }

    try:
        # Store events for cleanup
        down_events = []

        # Calculate modifier flags
        flags = 0
        for key in keys:
            if key == KEY_CODES['CMD']:
                flags |= Quartz.kCGEventFlagMaskCommand
            elif key == KEY_CODES['OPT']:
                flags |= Quartz.kCGEventFlagMaskAlternate
            elif key == KEY_CODES['SHIFT']:
                flags |= Quartz.kCGEventFlagMaskShift
            elif key == KEY_CODES['CTRL']:
                flags |= Quartz.kCGEventFlagMaskControl

        # Press all modifier keys first
        for key in keys[:-1]:  # All keys except the last one
            down_event = Quartz.CGEventCreateKeyboardEvent(None, key, True)
            Quartz.CGEventSetFlags(down_event, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
            down_events.append((key, down_event))

        # Press and release the last key (usually the non-modifier key)
        last_key = keys[-1]
        down_event = Quartz.CGEventCreateKeyboardEvent(None, last_key, True)
        up_event = Quartz.CGEventCreateKeyboardEvent(None, last_key, False)

        # Set flags for both down and up events
        Quartz.CGEventSetFlags(down_event, flags)
        Quartz.CGEventSetFlags(up_event, flags)

        # Post the events
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)

        # Release all modifier keys in reverse order
        for key, _ in reversed(down_events):
            up_event = Quartz.CGEventCreateKeyboardEvent(None, key, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)

        # Give events some processing time
        time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error simulating keypress: {e}")


KEY_CODES = {
    # 字母键
    'A': 0x00,
    'B': 0x0B,
    'C': 0x08,
    'D': 0x02,
    'E': 0x0E,
    'F': 0x03,
    'G': 0x05,
    'H': 0x04,
    'I': 0x22,
    'J': 0x26,
    'K': 0x28,
    'L': 0x25,
    'M': 0x2E,
    'N': 0x2D,
    'O': 0x1F,
    'P': 0x23,
    'Q': 0x0C,
    'R': 0x0F,
    'S': 0x01,
    'T': 0x11,
    'U': 0x20,
    'V': 0x09,
    'W': 0x0D,
    'X': 0x07,
    'Y': 0x10,
    'Z': 0x06,

    # 数字键
    '0': 0x1D,
    '1': 0x12,
    '2': 0x13,
    '3': 0x14,
    '4': 0x15,
    '5': 0x17,
    '6': 0x16,
    '7': 0x1A,
    '8': 0x1C,
    '9': 0x19,

    # 修饰键
    'CMD': 0x37,
    'SHIFT': 0x38,
    'CAPS_LOCK': 0x39,
    'OPT': 0x3A,
    'CTRL': 0x3B,
    'RIGHT_SHIFT': 0x3C,
    'RIGHT_OPT': 0x3D,
    'RIGHT_CTRL': 0x3E,
    'FN': 0x3F,

    # 功能键
    'F1': 0x7A,
    'F2': 0x78,
    'F3': 0x63,
    'F4': 0x76,
    'F5': 0x60,
    'F6': 0x61,
    'F7': 0x62,
    'F8': 0x64,
    'F9': 0x65,
    'F10': 0x6D,
    'F11': 0x67,
    'F12': 0x6F,

    # 特殊键
    'RETURN': 0x24,
    'TAB': 0x30,
    'SPACE': 0x31,
    'DELETE': 0x33,
    'ESC': 0x35,
    'FORWARD_DELETE': 0x75,
    'HOME': 0x73,
    'END': 0x77,
    'PAGE_UP': 0x74,
    'PAGE_DOWN': 0x79,
    'LEFT_ARROW': 0x7B,
    'RIGHT_ARROW': 0x7C,
    'DOWN_ARROW': 0x7D,
    'UP_ARROW': 0x7E,

    # 其他常用键
    'ENTER': 0x4C,
    'HELP': 0x72,
    'MUTE': 0x4A,
    'VOLUME_UP': 0x48,
    'VOLUME_DOWN': 0x49
}
