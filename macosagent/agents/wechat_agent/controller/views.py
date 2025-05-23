from pydantic import BaseModel, model_validator


# Action Input Models
class ClickElementAction(BaseModel):
	index: int


class RightClickElementAction(BaseModel):
	index: int


class InputAction(BaseModel):
	index: int
	text: str


class ScrollAction(BaseModel):
	index: int
	amount: int | None = None


class PasteAction(BaseModel):
	index: int


class CopyAction(BaseModel):
	index: int


class SendAction(BaseModel):
	index: int

class ExtractContent(BaseModel):
	target: str
	content: str

# class ModifyClipboardTextAction(BaseModel):
# 	requirement_text: str


class DoneAction(BaseModel):
	text: str
	success: bool


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
