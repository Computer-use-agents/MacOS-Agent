import subprocess
import os 
import shutil

from smolagents import Tool
from AppKit import NSPasteboard, NSURL


class Paste(Tool):
    name = 'paste_finder'
    description = "A tool can paste file or folder into the desirable path."
    inputs = {
        "path": {"description": "the folder path for pasting", "type": "string"}
    }
    output_type = "string"

    def forward(self, path):

        file_url_uti = 'public.file-url'
        pb = NSPasteboard.generalPasteboard()
        items = pb.pasteboardItems()
        
        if not items:
            return

        flag=0
        for item in items:
            file_url = item.stringForType_(file_url_uti)
            if file_url:
                src_path = NSURL.URLWithString_(file_url).path()
                filename = os.path.basename(src_path)
                dest_path = os.path.join(path, filename)
                    
                try:
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)
                    else:
                        shutil.copy2(src_path, dest_path)
                except Exception as e:
                    flag=1
                    print(f"An error occurred: {e}")
        if flag==0:
            return "Paste the folder or file with no explicit errors."
        else:
            return "Some errors are occurred in pasting the folder or file."