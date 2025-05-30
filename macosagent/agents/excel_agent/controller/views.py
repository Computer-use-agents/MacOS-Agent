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

class ComputerUseAction(BaseModel):
    goal_description: str
    
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


class OpenExcelAction(BaseModel):
	file_path: str

class SaveFileAction(BaseModel):
	file_path: str


class SaveAndCloseAction(BaseModel):
    file_path: str	
    

class InsertCellTextAction(BaseModel):
    file_path: str
    file_save_path: str
    sheet_name: Optional[str] = 'Sheet1'
    cell_address: str 
    insert_text: str
    insert_pos: Optional[int] = 0
# file_path, file_save_path, sheet_name, cell_address,insert_text, insert_pos

class CreateExcelAction(BaseModel):
    file_path: str
    

class DeleteCellTextAction(BaseModel):
    file_path: str
    file_save_path: str
    sheet_name: Optional[str] = 'Sheet1'
    cell_address: str 
    