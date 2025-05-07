import enum
import json
import logging
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Generic, TypeVar

import icalendar
import pyautogui
import pynput

# from lmnr.sdk.laminar import Laminar
from pydantic import BaseModel

from macosagent.agents.calendar_agent.agent.views import ActionModel, ActionResult
from macosagent.agents.calendar_agent.calendar.context import CalendarContext
from macosagent.agents.calendar_agent.controller.registry.service import Registry
from macosagent.agents.calendar_agent.controller.views import (
    ClickElementAction,
    CreateCalendarEventAction,
    DoneAction,
    InputTextAction,
)

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
        async def click_element(params: ClickElementAction, context: CalendarContext):
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
                elif element[0]["role"] == "AXButton":
                    pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                else:
                    pyautogui.moveTo(x=x, y=y)
                    pynput.mouse.Controller().click(button=pynput.mouse.Button.left, count=2)
                return ActionResult(is_done=False, success=True, extracted_content=f"🖱️  Clicked button with index {params.index}", include_in_memory=True)
            except Exception as e:
                logger.error(f"Error clicking element: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Input text into the element",
            param_model=InputTextAction,
        )
        async def input_text(params: InputTextAction, context: CalendarContext):
            index = params.index
            element = [item for item in context.state.accessibility_tree_json if item["id"] == index]
            x, y, w, h = element[0]["bbox"]
            offset = context.state.offset
            x = int(x + offset[0] + w/2)
            y = int(y + offset[1] + h/2)
            try:
                logger.info(f"Inputting text {params.text} into element {element[0]}")
                pyautogui.click(x=x, y=y, clicks=1, interval=0.1, button='left')
                pyautogui.write(escape_single_quotes(params.text), interval=0.1)
                pyautogui.press('enter')
                return ActionResult(is_done=False, success=True, extracted_content= f'⌨️  Input {params.text} into index {params.index}', include_in_memory=True)
            except Exception as e:
                logger.error(f"Error inputting text: {e}")
                return ActionResult(is_done=False, success=False, extracted_content=str(e), include_in_memory=True)

        @self.registry.action(
            "Create calendar event",
            param_model=CreateCalendarEventAction,
        )
        async def create_calendar_event(params: CreateCalendarEventAction):
            cal = icalendar.Calendar()
            event = icalendar.Event()
            event.add('summary', params.summary)
            event.add('description', params.description)

            try:
                date_start = parse_datetime(params.date_start)
                date_end = parse_datetime(params.date_end)
                event.add('dtstart', date_start)
                event.add('dtend', date_end)
            except ValueError as e:
                logger.error(f"Error parsing dates: {e}")
                raise
            cal.add_component(event)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ics') as f:
                f.write(cal.to_ical())
                f.flush()
                logger.info(f"Created calendar event {f.name}")
                subprocess.run(['open', f.name], check=False)
            return ActionResult(is_done=False, success=True, extracted_content=f"🗓️  Created calendar event {params.summary}")

    async def act(
        self,
        action: ActionModel,
        calendar_context: CalendarContext,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    # with Laminar.start_as_current_span(
                    # 	name=action_name,
                    # 	input={
                    # 		'action': action_name,
                    # 		'params': params,
                    # 	},
                    # 	span_type='TOOL',
                    # ):
                    result = await self.registry.execute_action(
                        action_name,
                        params,
                        calendar_context=calendar_context,
                    )

                    # Laminar.set_span_output(result)

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




def get_calendar_events(start_date, end_date):
    # Format dates for AppleScript (YYYY-MM-DD HH:MM:SS)
    logger.info(f"Start date: {start_date}, End date: {end_date}")
    script = f'''
    tell application "Calendar"
        set startDate to date "{start_date}"
        set endDate to date "{end_date}"
        set eventList to {{}}
        
        try
            repeat with calendarAccount in calendars
                set eventList to eventList & (every event of calendarAccount whose start date is greater than or equal to startDate and start date is less than or equal to endDate)
            end repeat
            
            set output to ""
            repeat with theEvent in eventList
                set output to output & "Event: " & summary of theEvent & "\n"
                set output to output & "Start: " & ((start date of theEvent) as «class isot» as string) & "\n"
                set output to output & "End: " & ((end date of theEvent) as «class isot» as string) & "\n"
                set output to output & "-------------------\n"
            end repeat
            
            return output
        on error errMsg
            return "Error: " & errMsg
        end try
    end tell
    '''
    logger.info(f"Script: {script}")
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, encoding='utf-8', check=False)
        if result.returncode != 0:
            return f"Error executing AppleScript: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Python error: {e!s}"


def parse_datetime(date_string: str) -> datetime:
    """Parse different datetime formats and return a datetime object."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",  # 2025-03-22T09:00:00
        "%Y-%m-%d",           # 2025-03-22
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            # If only date is provided, set default time to 00:00:00
            if fmt == "%Y-%m-%d":
                return dt.replace(hour=0, minute=0, second=0)
            return dt
        except ValueError:
            continue

    raise ValueError(f"Unsupported date format: {date_string}. Expected formats: YYYY-MM-DD or YYYY-MM-DDThh:mm:ss")

