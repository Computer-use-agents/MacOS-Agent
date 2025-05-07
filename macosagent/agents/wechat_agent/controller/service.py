import asyncio
import json
import enum
import logging
from typing import Dict, Generic, Optional, Type, TypeVar
import subprocess
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
import tempfile
from datetime import datetime, timedelta
# from lmnr.sdk.laminar import Laminar
from pydantic import BaseModel

from macosagent.agents.wechat_agent.controller.registry.service import Registry
from macosagent.agents.wechat_agent.wechat.context import WechatContext
from macosagent.agents.wechat_agent.controller.views import ClickElementAction, InputAction, DoneAction, ScrollAction, PasteAction, CopyAction, RightClickElementAction, SendAction
from macosagent.agents.wechat_agent.agent.views import ActionResult, ActionModel
import pyautogui
import pyperclip
import re
import time

#from macosagent.agents.wechat_agent.agent.llm import create_gpt_4o_tool  
from omegaconf import DictConfig, OmegaConf
import hydra

logger = logging.getLogger(__name__)

Context = TypeVar('Context')


class Controller(Generic[Context]):
    def __init__(
        self,
        exclude_actions: list[str] = [],
        output_model: Optional[Type[BaseModel]] = None,
    ):
        self.registry = Registry[Context](exclude_actions)

        # self.SYSTEM_PROMPT = """Edit the text according to the reduction requirements and output only the revised version—no explanations or introductions."""

        # cfg = hydra.compose(config_name="llm.yaml")

        # self.MODEL = cfg.llm.model
        # self.client = create_gpt_4o_tool(cfg.llm)

        """Register all default browser actions"""

        if output_model is not None:
            # Create a new model that extends the output model with success parameter
            class ExtendedOutputModel(BaseModel):  # type: ignore
                success: bool = True
                data: output_model

            @self.registry.action(
                'Complete task - with return text and if the task is finished (success=True) or not yet completly finished (success=False), because last step is reached',
                param_model=ExtendedOutputModel,
            )
            async def done(params: ExtendedOutputModel):
                output_dict = params.data.model_dump()

                for key, value in output_dict.items():
                    if isinstance(value, enum.Enum):
                        output_dict[key] = value.value

                return ActionResult(is_done=True, success=params.success, extracted_content=json.dumps(output_dict))
        else:
            @self.registry.action(
                'Complete task - with return text and if the task is finished (success=True) or not yet completly finished (success=False), because last step is reached',
                param_model=DoneAction,
            )
            async def done(params: DoneAction):
                return ActionResult(is_done=True, success=params.success, extracted_content=params.text)

        @self.registry.action(
            "Click element",
            param_model=ClickElementAction,
        )
        async def click_element(params: ClickElementAction, context: WechatContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            logger.info(f"Clicking element {element[0]}")
            try:
                logger.info(f"clicking element at {x}, {y}")
                pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                return ActionResult(is_done=False, success=True, extracted_content=f"🖱️  Clicked button with index {params.index}", include_in_memory=True)
            except Exception as e:
                logger.error(f"Error clicking element: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Right-Click element",
            param_model=RightClickElementAction,
        )
        async def right_click_element(params: RightClickElementAction, context: WechatContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            logger.info(f"Right-clicking element {element[0]}")
            try:
                logger.info(f"right-clicking element at {x}, {y}")
                pyautogui.click(x=x, y=y, clicks=2, interval=0.1, button='right')
                return ActionResult(is_done=False, success=True, extracted_content=f"🖱️  Clicked button with index {params.index}", include_in_memory=True)
            except Exception as e:
                logger.error(f"Error right-clicking element: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Input into the element",
            param_model=InputAction,
        )
        async def inputs(params: InputAction, context: WechatContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)

            # original_clipboard_content = pyperclip.paste()
            try:
                logger.info(f"Inputting text {params.text} into element {element[0]}")
                pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                # pyautogui.write(escape_single_quotes(params.text), interval=0.1)
                pyperclip.copy(params.text)
                pyautogui.hotkey('command', 'a')
                time.sleep(0.1) 
                pyautogui.hotkey('command', 'v')
                time.sleep(0.1) 
                pyautogui.press('enter')

                # pyperclip.copy(original_clipboard_content)

                return ActionResult(is_done=False, success=True, extracted_content= f'⌨️  Input {params.text} into index {params.index}', include_in_memory=True)
            except Exception as e:
                # pyperclip.copy(original_clipboard_content)
                logger.error(f"Error inputting text: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Scroll element",
            param_model=ScrollAction,
        )
        async def scroll(params: ScrollAction, context: WechatContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            logger.info(f"Scroll element {element[0]}")
            try:
                amount = params.amount if params.amount is not None else 0  # Default to scrolling one page if amount is None
                logger.info(f"Scrolling {amount} pixels")
                # pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                pyautogui.moveTo(x, y, duration=0.1)
                pyautogui.scroll(amount)  # Use pyautogui to scroll by 'amount' pixels
                return ActionResult(is_done=False, success=True, extracted_content=f"🌀  Scrolled {amount} pixels", include_in_memory=True)
            except Exception as e:
                logger.error(f"Error scrolling: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Paste clipboard text",
            param_model=PasteAction,
        )
        async def paste(params: PasteAction, context: WechatContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            logger.info(f"Paste to element {element[0]}")
            try:
                pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                time.sleep(0.1) 
                # pyautogui.press('end')
                pyautogui.hotkey('command', 'a')
                time.sleep(0.1) 
                pyautogui.hotkey('command', 'v')
                return ActionResult(is_done=False, success=True, extracted_content=f"📄 Pasted text from clipboard", include_in_memory=True)
            except Exception as e:
                logger.error(f"Error pasting text: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)
            
        @self.registry.action(
            "Select text and copy",
            param_model=CopyAction,
        )
        async def copy_text(params: CopyAction, context: WechatContext):
            try:
                index = params.index
                element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
                x, y, w, h = element[0]["bbox"]
                offset = context.state.offset

                # start_x = int(x + offset[0] + 5)
                # start_y = int(y + offset[1] + 5)

                # end_x = int(x + offset[0] + w - 5)  
                # end_y = int(y + offset[1] + h - 5)

                # pyautogui.moveTo(start_x, start_y, duration=0.2)
                # pyautogui.dragTo(end_x, end_y, duration=1.5, button='left')

                x = int(x + offset[0] + w/2)
                y = int(y + offset[1] + h/2)

                pyautogui.click(x=x, y=y, clicks=2, interval=0.1, button='left')
                time.sleep(0.1) 
                pyautogui.hotkey('command', 'a')
                pyautogui.hotkey('command', 'c')

                return ActionResult(is_done=False, success=True, extracted_content=f"📋 Copied selected text from index {params.index}", include_in_memory=True)
            
            except Exception as e:
                logger.error(f"Error copying text: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)
            
        @self.registry.action(
            "Send message",
            param_model=SendAction,
        )
        async def send(params: SendAction, context: WechatContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            logger.info(f"Paste to element {element[0]}")
            try:
                pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                time.sleep(0.1) 
                pyautogui.press('enter')
                return ActionResult(is_done=False, success=True, extracted_content=f"📄 Send message in index {params.index}", include_in_memory=True)
            except Exception as e:
                logger.error(f"Error pasting text: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        # @self.registry.action(
        #     "Modify clipboard text",
        #     param_model=ModifyClipboardTextAction,
        # )
        # async def modify_clipboard_text(params: ModifyClipboardTextAction, context: WechatContext):
        #     try:
        #         copied_text = pyperclip.paste()

        #         text = f"""
        #         Input Text: 
        #         {copied_text}

        #         Reduction Requirements:
        #         {params.requirement_text}

        #         Output only the revised text.
        #         """

        #         messages = [
        #             {"role": "system", "content": self.SYSTEM_PROMPT},
        #             {"role": "user", "content": [
        #                 {"type": "text", "text": text}
        #             ]},
        #         ]

        #         response = self.client.chat.completions.create(
        #             model=self.MODEL,
        #             messages=messages,
        #             max_tokens=256,
        #             temperature=1.0
        #             # response_format = "json"
        #         )

        #         content = response.choices[0].message.content
        #         logger.info(f"Filtered text: {content}")

        #         pyperclip.copy(content)

        #         return ActionResult(is_done=False, success=True, extracted_content=f"📋 Modified clipboard text to {content} according to {params.requirement_text}", include_in_memory=True)
            
        #     except Exception as e:
        #         logger.error(f"Error copying text: {e}")
        #         return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)
            

    async def act(
        self,
        action: ActionModel,
        wechat_context: WechatContext,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    result = await self.registry.execute_action(
                        action_name,
                        params,
                        wechat_context=wechat_context,
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
    pattern = r"(?<!\\)'"
    return re.sub(pattern, r"\\'", text)
