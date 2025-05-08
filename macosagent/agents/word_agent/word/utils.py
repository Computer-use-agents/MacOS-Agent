import re
import random
from PIL import Image, ImageFont


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

def get_random_color():
	"""Generate a random pleasing color with good visibility"""
	# Use pastel-like colors by mixing with white
	r = random.randint(100, 255)
	g = random.randint(100, 255)
	b = random.randint(100, 255)
	return (r, g, b)

class BoxDrawer():
	def __init__(self):
		self.bounding_box_counter = 0
		self.element_white_list = [
			'AXCell','AXMenuButton','AXScrollBar','AXLayoutArea','AXButton', 'AXRadioButton','AXValueIndicator','AXCheckBox','AXComboBox'
		]
		# AXCell: 左侧slide 单击
		# AXMenuButton： 菜单栏单击  
		# 需要： AXCell,AXMenuButton,AXScrollBar,AXLayoutArea,AXButton, AXRadioButton,AXValueIndicator,AXCheckBox,AXComboBox
		# 不需要的： AXGroup， AXList,AXScrollArea, AXSplitter,AXStaticText,AXSplitGroup
		# self.element_white_list = [
		# 	"AXEnabled"
		# ]
		self.white_list_enabled = True
		
	def draw_bounding_box(self, draw, element, offset=(0, 0)):
		"""Draw a bounding box around an element"""		# print("Draw bounding box", element)
		bounding_box = element["attributes"]["AXFrame"]
		desc = element["attributes"]["AXRoleDescription"] if "AXRoleDescription" in element["attributes"] else ""
		role = element["role"] if "role" in element else ""
		# print("Try draw bounding box", role, role in self.element_white_list, element)
		draw_enabled = False
		if self.white_list_enabled:
			draw_enabled = bounding_box is not None and role in self.element_white_list
		else:
			draw_enabled = bounding_box is not None
		if draw_enabled:
			try:
				x, y, w, h = parse_axvalue_bounds(bounding_box, offset)
				if w == 0 or h == 0:
					return
					
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
					"help": element["attributes"]["AXHelp"] if "AXHelp" in element["attributes"] else "",
					"bbox": (x, y, w, h)
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
		try:
			box = self.draw_bounding_box(draw, element, offset=offset)
			if box:
				boxes += [box]
		except Exception as e:
			# print(f"Error processing tree: {e} drop children:", len(element.get('children', [])))
			return boxes
		
		# Process children
		children = element.get('children', [])
		for child in children:
			boxes += self.process_tree(draw, child, offset)
		return boxes
		
def draw_bounding_box(draw, element, offset=(0, 0)):
	"""Draw a bounding box around an element"""
	global box_counter
	# print("Draw bounding box", element)
	bounding_box = element["attributes"]["AXFrame"]
	desc = element["attributes"]["AXRoleDescription"] if "AXRoleDescription" in element["attributes"] else ""
	
	if bounding_box:
		try:
			x, y, w, h = parse_axvalue_bounds(bounding_box, offset)
			if w == 0 or h == 0:
				return
				
			# Increment counter and generate unique color
			box_counter += 1
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
			
			# print(f"Drew box {box_counter} with color {color}")
			return {
				"id": box_counter,
				"desc": desc,
				"role": element["role"],
				"role_description": element["attributes"]["AXRoleDescription"] if "AXRoleDescription" in element["attributes"] else "",
				"subrole": element["attributes"]["AXSubrole"] if "AXSubrole" in element["attributes"] else None,
				"bbox": (x, y, w, h)
			}
		except ValueError as e:
			raise e
		return None

def process_tree(draw, element, offset=(0, 0)):
	"""Recursively process the accessibility tree and draw boxes for interactive elements"""
	# Handle both list and dictionary inputs
	boxes = []
	if isinstance(element, list):
		for item in element:
			boxes += process_tree(draw, item, offset)
		return boxes
		
	# Check if element is interactive
	box = draw_bounding_box(draw, element, offset=offset)
	if box:
		boxes += [box]
	
	# Process children
	children = element.get('children', [])
	for child in children:
		boxes += process_tree(draw, child, offset)
	return boxes
