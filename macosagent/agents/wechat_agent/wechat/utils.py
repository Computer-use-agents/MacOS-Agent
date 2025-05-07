import re
import random
from PIL import Image, ImageDraw, ImageFont


def parse_axvalue_bounds(bounds_str, offset=(0, 0)):
	"""
	Parse AXValue string containing bounds information into (x, y, w, h)
	Example input: "<AXValue 0x138e3fbe0> {value = x:603.500000 y:46.000000 w:65.000000 h:25.000000 type = kAXValueCGRectType}"
	Returns: tuple of floats (x, y, w, h)
	"""
	# Regular expression to match x, y, w, h values
	pattern = r'x:([-]?\d+\.?\d*)\s*y:([-]?\d+\.?\d*)\s*w:([-]?\d+\.?\d*)\s*h:([-]?\d+\.?\d*)'
	
	match = re.search(pattern, bounds_str)
	if match:
		# Convert all matched values to float
		x, y, w, h = map(float, match.groups())
		return (x-offset[0], y-offset[1], w, h)
	else:
		# print(f"Could not parse bounds from string: {bounds_str}")
		raise ValueError(f"Could not parse bounds from string: {bounds_str}")

def parse_rect_bounds(rect, offset=(0, 0)):
    """
    Parse rect information containing bounds into (x, y, w, h)
    """
    x = rect["left"]
    y = rect["top"]
    w = rect["width"]
    h = rect["height"]

    return (x-offset[0], y-offset[1], w, h)

def get_random_color():
    """Generate a random pleasing color with good visibility"""
    return (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

class BoxDrawer():
	def __init__(self):
		self.bounding_box_counter = 0
	
	def draw_bounding_box(self, draw, element, offset=(0, 0)):
		"""Draw a bounding box around an element"""		# ("Draw bounding box", element)

		try:
			bounding_box = element["attributes"]["AXFrame"]
		except:
			return None
		
		# desc = element["attributes"]["AXRoleDescription"] if "AXRoleDescription" in element["attributes"] else ""
		if "title" in element:
			desc = element["title"]
		elif "AXHelp" in element["attributes"]:
			desc = element["attributes"]["AXHelp"]
		elif "AXDescription" in element["attributes"]:
			desc = element["attributes"]["AXDescription"]
		elif "AXRoleDescription" in element["attributes"]:
			desc = element["attributes"]["AXRoleDescription"]
		else:
			desc = ""

		if bounding_box:
			try:
				x, y, w, h = parse_axvalue_bounds(bounding_box, offset)
				if w == 0 or h == 0:
					return None
					
				# Increment counter and generate unique color
				self.bounding_box_counter += 1
				color = get_random_color()
				
				# print(f"Drawing box at: ({x}, {y}) -> ({x+w}, {y+h})")
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
					
				label = f"{self.bounding_box_counter}"
				
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
				
				# print(f"Drew box {box_counter} with color {color}")
				return {
					"id": self.bounding_box_counter,
					"desc": desc,
					"role": element["role"],
					"role_description": element["attributes"]["AXRoleDescription"] if "AXRoleDescription" in element["attributes"] else "",
					"subrole": element["attributes"]["AXSubrole"] if "AXSubrole" in element["attributes"] else None,
					"bbox": (x, y, w, h),
					"visibility": "visible" if self.check_overlap(x, y, w, h, img_width, img_height) else "invisible"
				}
			except ValueError as e:
				raise e
			return None
		
	def process_tree(self, draw, element, offset=(0, 0)):
		"""Recursively process the accessibility tree and draw boxes for interactive elements"""
		# Handle both list and dictionary inputs
		boxes = []
		if isinstance(element, list):
			for item in element:
				boxes += self.process_tree(draw, item, offset)
			return boxes
			
		# Check if element is interactive
		box = self.draw_bounding_box(draw, element, offset=offset)
		if box:
			boxes += [box]
		
		# Process children
		children = element.get('children', [])
		for child in children:
			boxes += self.process_tree(draw, child, offset)
		return boxes
	
	def check_overlap(self, x, y, w, h, img_width, img_height):
		inter_x1 = max(x, 0)
		inter_y1 = max(y, 0)
		inter_x2 = min(x + w, img_width)
		inter_y2 = min(y + h, img_height)

		inter_width = inter_x2 - inter_x1
		inter_height = inter_y2 - inter_y1

		return inter_width > 0 and inter_height > 0
