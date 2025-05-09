import subprocess
import os 

from smolagents import Tool



class Open(Tool):
    name = 'open_finder'
    description = "A tool can open the Finder for further operations."
    inputs = {
        "folder_path": {"description": "the folder path that need to be opened", "type": "string", 'nullable': True}
    }
    output_type = "string"


    def forward(self, folder_path=None):
        if folder_path==None:
            try:
                subprocess.run(["open", "-a", "Finder"])

                applescript = """
                tell application "System Events"
                    tell application "Finder" to activate
                    keystroke "f" using {control down, command down}
                end tell      
                """          
                subprocess.run(['osascript', '-e', applescript], check=True)

                return "Opening the finder with no explicit errors."
            except:
                return "Some errors are occurred in opening the finder."
        else:
            if os.path.exists(folder_path):
                try:
                    subprocess.run(['open', '-a', "Finder", folder_path])

                    applescript = """
                    tell application "System Events"
                        tell application "Finder" to activate
                        keystroke "f" using {control down, command down}
                    end tell      
                    """          
                    subprocess.run(['osascript', '-e', applescript], check=True)

                    return "Opening an existing folder path via the finder with no explicit errors."
                except:
                    return "Some errors are occurred in opening an existing folder path via the finder."   
            else:
                try:
                    os.makedirs(folder_path, exist_ok=True)
                    subprocess.run(['open', '-a', "Finder", folder_path])

                    applescript = """
                    tell application "System Events"
                        tell application "Finder" to activate
                        keystroke "f" using {control down, command down}
                    end tell      
                    """          
                    subprocess.run(['osascript', '-e', applescript], check=True)

                    return "Opening a new folder path via the finder with no explicit errors."
                except:
                    return "Some errors are occurred in opening a new folder path via the finder."                                

