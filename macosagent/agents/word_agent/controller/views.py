from typing import Optional, Tuple,List

from pydantic import BaseModel, model_validator




class ClickElementAction(BaseModel):
	index: int


class InputTextAction(BaseModel):
    insert_x_position: int
    insert_y_position: int 
    text: str

class DoneAction(BaseModel):
	text: str
	success: bool



class OpenTabAction(BaseModel):
	url: str


class ScrollAction(BaseModel):
	amount: Optional[int] = None  # The number of pixels to scroll. If None, scroll down/up one page


class SendKeysAction(BaseModel):
	keys: str


class ExtractPageContentAction(BaseModel):
	value: str


class NoParamsAction(BaseModel):
	"""
	Accepts absolutely anything in the incoming data
	and discards it, so the final parsed model is empty.
	"""

	@model_validator(mode='before')
	def ignore_all_inputs(cls, values):
		# No matter what the user sends, discard it and return empty.
		return {}

	class Config:
		# If you want to silently allow unknown fields at top-level,
		# set extra = 'allow' as well:
		extra = 'allow'


class OpenWordAction(BaseModel):
	file_path: str

class SaveFileAction(BaseModel):
	file_path: str

class ConvertFileAction(BaseModel):
    file_path: str

# from typing import Optional, List, Tuple, Annotated
# from pydantic import BaseModel, Field
# RangeTuple = Annotated[
#     Tuple[int, int, int],
#     Field(..., json_schema={
#         "type": "array",
#         "items": [
#             {"type": "integer", "description": "段落索引"},
#             {"type": "integer", "description": "起始位置"},
#             {"type": "integer", "description": "段落索引"}
#         ],
#         "minItems": 3,
#         "maxItems": 3
#     })
# ]

# RangeList = Annotated[
# 	List[RangeTuple],
# 	Field(..., json_schema={
#         "type": "list",
#         "items": [
#             {"type": "RangeTuple", "description": "描述修改的作用范围"},
#         ],
#         "minItems": 1,
#         "maxItems": 100
#     })
# ]

    
class ModifyRangeStylesAction(BaseModel):
    file_save_path: str
    paragraph_to_modify: int 
    start_index: int
    end_index: int  
    font_name: str
    font_size: float
    font_color: Optional [str] = 'FFFFFF'
    left_indent_cm: Optional[float] = None
    first_line_indent_cm: Optional[float] = None

# class GeneratePowerPointAction(BaseModel):
#     file_path: str
    


# def delete_image_function(doc_path, output_path, image_index):
# def delete_text_ranges_function(doc_path, output_path, paragraph_index, start_pos, end_pos):
# def delete_tables_function(doc_path, output_path, table_index):
    
class DeleteImageAction(BaseModel):
    file_save_path: str
    image_index: int

class DeleteTextRangesAction(BaseModel):
    file_save_path: str
    paragraph_index: int
    start_pos: int
    end_pos: int 

class DeleteTableAction(BaseModel):
    file_save_path: str
    table_index: int 
    
class SaveAndCloseAction(BaseModel):
    file_path: str	
   
class ComputerUseAction(BaseModel):
    goal_description: str
    
    

class InsertImageAction(BaseModel):
    doc_path: str
    file_save_path: str
    image_path: str
    insert_position: int
    
class InsertTableAction(BaseModel):
    doc_path: str
    target_para: int
    rows: int 
    cols: int 
    cols: int 
    data: List

class CreateDocxAction(BaseModel):
    file_path: str	