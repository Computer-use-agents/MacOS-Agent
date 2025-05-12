import base64
import subprocess

from smolagents import Tool

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class ReadContent(Tool):
    name = 'read_content'
    description = "A tool can extract contents (such as files and subfolders) of currently opened folder in Finder."
    inputs = {
    }
    output_type = "string"

    def forward(self):
        applescript = """
        tell application "Finder"
            if (count of Finder windows) > 0 then
                set theWindow to front window
                set theFolder to (target of theWindow as alias)
                set folderPath to POSIX path of theFolder
                set fileList to {}
                set folderList to {}
                
                -- 获取文件
                set theFiles to every file of theFolder
                repeat with aFile in theFiles
                    set end of fileList to name of aFile
                end repeat
                
                -- 获取子文件夹
                set theFolders to every folder of theFolder
                repeat with aFolder in theFolders
                    set end of folderList to name of aFolder
                end repeat
                
                return {folderPath:folderPath, files:fileList, folders:folderList}
            else
                return "no Finder window open"
            end if
        end tell
        """
        
        try:
            result = subprocess.run(['osascript', '-e', applescript], 
                                capture_output=True, text=True, check=True)
            # 解析 AppleScript 输出
            if result.stdout.strip() == "no Finder window open":
                return "No Finder window open"
            else:
                output = result.stdout.strip()
                # 简单提取各部分内容

                folderPath_index= output.index('folderPath:')
                filePath_index= output.index('file:')
                subfolderPath_index= output.index('folder:')

                folderPath = output[folderPath_index+len('folderPath:'):filePath_index]
                files = output[filePath_index+len('file:'):subfolderPath_index]
                subfolders = output[subfolderPath_index+len('folder:'):]
                
                return (f"Current Finder path: {folderPath}\n"
                        f"Files: {files}\n"
                        f"Folders: {subfolders}")
        except subprocess.CalledProcessError as e:
            return f"Execution AppleScript Failure: {e}"
