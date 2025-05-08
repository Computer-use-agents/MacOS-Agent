import os 
import shutil

from smolagents import Tool

class Move(Tool):
    name = 'move_finder'
    description = "A tool can move file or folder into a desirable path."
    inputs = {
        "src_path": {"description": "the file or folder path that need to be moved", "type": "string"},
        "dst_folder": {"description": "the path that need to paste the file or folder", "type": "string"}
    }
    output_type = "string"


    def forward(self, src_path, dst_folder):
        try:
            os.makedirs(os.path.dirname(dst_folder), exist_ok=True)
            shutil.move(src_path, dst_folder)
            return "Move the folder or file with no explicit errors."
        except Exception as e:
            return "Some errors are occurred in moving the folder or file."
