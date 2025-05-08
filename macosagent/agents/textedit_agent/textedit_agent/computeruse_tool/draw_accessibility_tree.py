import json
import re
import random

from PIL import Image, ImageDraw, ImageFont
from importlib.resources import files
from pathlib import Path

# global box_counter
box_counter = 0

class DrawTree():
    name = 'draw_accessibility_tree'
    description = "A tool extract elements with bounding boxes from the accessibility tree, and draw them on the screenshot"
    inputs = {
        "screenshot_path": {"description": "the path to the screenshot", "type": "string"},
        "accessibility_tree_path": {"description": "the plan to the json file of accessibility tree", "type": "string"}
    }
    output_type = "list"

    # save_path=str(files("textedit_agent").joinpath("save"))+'/'
    save_path = str(Path('macosagent/agents/textedit_agent/textedit_agent').joinpath("save"))+'/'

    if not Path(save_path).exists():
        Path(save_path).mkdir(parents=True, exist_ok=True)


    def parse_axvalue_bounds(self, bounds_str, offset=(0, 0)):
        """
        Parse AXValue string containing bounds information into (x, y, w, h)
        Example input: "<AXValue 0x138e3fbe0> {value = x:603.500000 y:46.000000 w:65.000000 h:25.000000 type = kAXValueCGRectType}"
        Returns: tuple of floats (x, y, w, h)
        """
        # Regular expression to match x, y, w, h values
        pattern = r'x:(\d+\.?\d*)\s*y:(\d+\.?\d*)\s*w:(\d+\.?\d*)\s*h:(\d+\.?\d*)'
        
        match = re.search(pattern, bounds_str)
        if match:
            # Convert all matched values to float
            x, y, w, h = map(float, match.groups())
            return [(x-offset[0], y-offset[1], w, h),(x, y, w, h)]
        else:
            raise ValueError(f"Could not parse bounds from string: {bounds_str}")

    def get_random_color(self):
        """Generate a random pleasing color with good visibility"""
        # Use pastel-like colors by mixing with white
        r = random.randint(100, 255)
        g = random.randint(100, 255)
        b = random.randint(100, 255)
        return (r, g, b)


    def draw_bounding_box(self, draw, element, offset=(0, 0)):
        
        """Draw a bounding box around an element"""
        global box_counter
        bounding_box = element["attributes"]["AXFrame"]
        desc = element["attributes"]["AXRoleDescription"]
        
        if bounding_box:
            try:
                coordinate_list = self.parse_axvalue_bounds(bounding_box, offset)
                x, y, w, h = coordinate_list[0]
                x_s, y_s, w_s, h_s = coordinate_list[1]
                if w == 0 or h == 0:
                    return
                    
                # Increment counter and generate unique color
                box_counter += 1
                color = self.get_random_color()
                
                img_width, img_height = draw.im.size
                
                scale_factor = 1.0
                x = x * scale_factor
                y = y * scale_factor
                w = w * scale_factor
                h = h * scale_factor
                
                x1 = max(0, min(x, img_width))
                y1 = max(0, min(y, img_height))
                x2 = max(0, min(x + w, img_width))
                y2 = max(0, min(y + h, img_height))
                
                # Draw rectangle with unique color
                draw.rectangle(
                    [(x1, y1), (x2, y2)],
                    outline=color,
                    width=2
                )
                
                # Add ID text inside the box
                font_size = min(12, int(h/2))  # Adjust font size based on box height
                try:
                    font = ImageFont.truetype("Arial", font_size)
                except:
                    font = ImageFont.load_default()
                    
                label = f"{box_counter}"
                
                # Get text size
                text_bbox = draw.textbbox((0, 0), label, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # Position text at upper left with small margin
                margin = 2
                text_x = x1 + margin
                text_y = y1 + margin
                
                # Add padding for the background rectangle
                padding = 2
                bg_x1 = text_x - padding
                bg_y1 = text_y - padding
                bg_x2 = text_x + text_width + padding
                bg_y2 = text_y + text_height + padding
                
                # Draw background rectangle
                draw.rectangle(
                    [(bg_x1, bg_y1), (bg_x2, bg_y2)],
                    fill=color,
                    outline=None
                )
                
                # Draw text in white
                draw.text((text_x, text_y), label, fill=(0, 0, 0), font=font)
                
                return {
                    "id": box_counter,
                    "desc": desc,
                    "role": element["role"],
                    "role_description": element["attributes"]["AXRoleDescription"],
                    "subrole": element["attributes"]["AXSubrole"] if "AXSubrole" in element["attributes"] else None,
                    "bbox": (x, y, w, h),
                    "bbox_screen": (x_s, y_s, w_s, h_s)
                }
            except ValueError as e:
                print(f"Error parsing bounds: {e}")


        
    def process_tree(self, draw, element, offset=(0, 0)):
        """Recursively process the accessibility tree and draw boxes for interactive elements"""
        # Handle both list and dictionary inputs
        boxes = []
        if isinstance(element, list):
            for item in element:
                boxes += self.process_tree(draw, item, offset)
            return boxes
            
        boxes += [self.draw_bounding_box(draw, element, offset=offset)]
        
        # Process children
        children = element.get('children', [])
        for child in children:
            boxes += self.process_tree(draw, child, offset)
        return boxes

    def forward(self, application, screenshot_path, accessibility_tree_path):
        global box_counter
        box_counter = 0

        with open(self.save_path+application+'_accessibility_tree.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        frame_list = self.parse_axvalue_bounds(data[0]["attributes"]["AXFrame"])
        frame=frame_list[0]
        offset = (int(frame[0]), int(frame[1]))
        w, h = frame[2], frame[3]
        background = Image.open(self.save_path+application+'_window.png').convert('RGB').resize((int(w), int(h)))
        
        # Create drawing object
        draw = ImageDraw.Draw(background)
        
        
        
        # Process the tree and draw bounding boxes
        boxes = self.process_tree(draw, data, offset)
        
        # Save the result
        background.save(self.save_path+application+'_with_boxes.png')
        with open(self.save_path+application+'_with_boxes.json', 'w') as f:
            json.dump(boxes, f, indent=2, ensure_ascii=False)

        return [self.save_path+f"{application}_with_boxes.png", self.save_path+application+'_with_boxes.json']




