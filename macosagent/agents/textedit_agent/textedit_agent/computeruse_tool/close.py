import subprocess

from smolagents import Tool


class Close(Tool):
    name = 'close_application'
    description = "A tool can clsoe one application."
    inputs = {
        "application_name": {"description": "the application name that need to be opened", "type": "string" }
    }
    output_type = "string"


    def forward(self, application_name):

        try:
            subprocess.run(["osascript", "-e", 'quit app "TextEdit"'])
            return "Closing application with no explicit errors."
        except:
            return "Some errors are occurred in closing the application."