import subprocess
from smolagents import Tool


class Delete(Tool):
    name = 'delete_finder'
    description = "A tool can delete file or folder in the finder."
    inputs = {
        "file_path": {"description": "the file or folder path that need to be removed", "type": "string"}
    }
    output_type = "string"


    def forward(self, file_path):

        script = f'''
        tell application "Finder"
            delete POSIX file "{file_path}"
        end tell
        '''

        try:
            subprocess.run(["osascript", "-e", script])
            return "Delete the file or folder with no explicit errors."
        except:
            return "Some errors are occurred in delete the file or folder."