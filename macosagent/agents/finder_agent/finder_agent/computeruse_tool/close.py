import subprocess
import os 

from smolagents import Tool

class Close(Tool):
    name = 'close_finder'
    description = "A tool can clsoe the finder."
    inputs = {
    }
    output_type = "string"


    def forward(self):

        try:
            subprocess.run(["osascript", "-e", 'tell application "Finder" to quit'])
            return "Closing finder with no explicit errors."
        except:
            return "Some errors are occurred in closing the finder."