import subprocess
import os 

from smolagents import Tool
from typing import Optional


class Open(Tool):
    name = 'open_application'
    description = "Given a GUI task, a tool can open the TextEdit for further operations. MUST give a file path for this tool."
    inputs = {
        "application_name": {"description": "the application name that need to be opened", "type": "string" },
        "file_path": {"description": "the file path that need to be opened", "type": "string"}
    }
    output_type = "string"


    def forward(self, application_name, file_path):
        if os.path.exists(file_path):
            try:
                subprocess.run(['open', '-a', application_name, file_path])
                return "Opening an existing file with no explicit errors."
            except:
                return "Some errors are occurred in opening an existing file."
        else:
            with open(file_path, "w") as f:
                f.write("")
            try:
                subprocess.run(['open', '-a', application_name, file_path])
                return "Opening a new file with no explicit errors."
            except:
                return "Some errors are occurred in opening a new file."