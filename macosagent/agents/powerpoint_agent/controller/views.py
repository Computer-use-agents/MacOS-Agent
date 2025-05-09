from typing import Optional

from pydantic import BaseModel, model_validator


# Action Input Models
class SearchGoogleAction(BaseModel):
	query: str


class GoToUrlAction(BaseModel):
	url: str

 
class ClickElementAction(BaseModel):
	index: int


class InputTextAction(BaseModel):
    insert_x_position: int
    insert_y_position: int 
    text: str

class DoneAction(BaseModel):
	text: str
	success: bool


class SwitchTabAction(BaseModel):
	page_id: int


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


class OpenPowerPointAction(BaseModel):
	file_path: str

class SaveFileAction(BaseModel):
	file_path: str


class CreatePresentationAction(BaseModel):
    file_path: str	

class SaveAndCloseAction(BaseModel):
    file_path: str	

class ChangeSlideBackgroundColorAction(BaseModel):
    file_path: str
    slide_index: int
    hex_color: str
    file_save_path: str

from typing import Literal


class DeleteSlideItemAction(BaseModel):
    file_path: str
    file_save_path: str
    item_type: Literal['image', 'textbox', 'table']
    slide_index: int 
    item_index: int 
# input_path, output_path, slide_index, table_index=1

class ModifyTextRangeStyleAction(BaseModel):
    file_path: str
    file_save_path: str
    slide_index: int
    textbox_index: int 
    start_char: int
    end_char: Optional[int] = None
    font_name: Optional[str] = None
    font_size: Optional[int] = None
    hex_color: Optional[str] = None
    is_bold: Optional[bool] = None
    is_italic: Optional[bool] = None

class ComputerUseAction(BaseModel):
    goal_description: str
    


class InsertTextAction(BaseModel):
    file_path: str
    save_file_path: str
    slide_index: Optional[int] = 1
    font_size: int
    font_color_rgb_list: list
    align: str
    background_color: list
    left_offset: int
    top_offset: int 
    text: str
    width: Optional[int] = 3
    height: Optional[int] = 1

class InsertImageAction(BaseModel):
    slide_index: Optional[int] = 1
    file_path: str
    save_file_path: str
    left_offset: int
    top_offset: int 
    image_path: str
    width: Optional[int] = None
    height: Optional[int] = None
    keep_ratio: Optional[bool] = True

class InsertTableAction(BaseModel):
    slide_index: Optional[int] = 1
    file_path: str
    save_file_path: str
    left_offset: int
    top_offset: int 
    rows: int
    cols: int
    data: Optional[list] = None 
    col_widths: Optional[list] = None 
    table_style: Optional[str] = None 
    width: Optional[int] = 4
    height: Optional[int] = 2
