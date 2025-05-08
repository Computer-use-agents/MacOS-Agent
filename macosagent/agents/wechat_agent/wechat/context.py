"""
Wechat automation and accessibility processing.
"""

import logging
import uuid
from dataclasses import dataclass

from PIL import Image, ImageDraw

from macosagent.agents.wechat_agent.wechat.wechat import Wechat
from macosagent.agents.wechat_agent.wechat.utils import BoxDrawer, parse_axvalue_bounds, parse_rect_bounds

logger = logging.getLogger(__name__)


@dataclass
class WechatContextState:
    """
    State of the Wechat application context.
    """

    accessibility_tree: list[dict] | None = None
    screenshots: list[Image.Image] | None = None
    screenshots_som: list[Image.Image] | None = None
    accessibility_tree_json: list[dict] | None = None
    offset: tuple[int, int] | None = None


class WechatContext:
    def __init__(
        self,
        wechat: 'Wechat',
        state: WechatContextState | None = None,
    ):
        self.context_id = str(uuid.uuid4())
        logger.debug(f'Initializing new Wechat context with id: {self.context_id}')

        self.wechat = wechat
        self.state = state or WechatContextState()

    def get_state(self):
        windows, screenshots = self.wechat.get_app_windows()
        self.state.accessibility_tree = windows
        self.state.screenshots = screenshots
        
        # frame = parse_rect_bounds(windows[0]['rect'])
        frame = parse_axvalue_bounds(windows[0]["attributes"]["AXFrame"])
        offset = (int(frame[0]), int(frame[1]))
        self.state.offset = offset

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
            # interactive_elements_prompt += f"[{element['id']}]<{element['role']}>{element['desc']}</{element['role']}>\n"
            try:
                interactive_elements_prompt += f"[{element['id']}]<{element['role']}>{element['desc']}({element['visibility']})</{element['role']}>\n"
            except KeyError:
                # print(element)
                input("uedcu")
        return interactive_elements_prompt, self.state.accessibility_tree_json
