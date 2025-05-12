import subprocess
import os 

from smolagents import Tool

class Rename(Tool):
    name = 'rename'
    description = "A tool can rename folder or file in Finder."
    inputs = {
        "old_path": {"description": "the path of folder or file that need to be renamed", "type": "string" },
        "new_name": {"description": "the new name of the folder or file", "type": "string"}
    }
    output_type = "string"


    def forward(self, old_path, new_name):

        applescript = f"""
        tell application "Finder"
            set theItem to POSIX file "{old_path}" as alias
            set name of theItem to "{new_name}"
        end tell
        """
        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            return "Renaming the folder or file with no explicit errors."
        except subprocess.CalledProcessError as e:
            return(f"Some errors are occurred in opening an existing folder path via the finder: {e}")