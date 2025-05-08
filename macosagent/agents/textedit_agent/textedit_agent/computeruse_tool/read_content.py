import base64
import subprocess

from smolagents import Tool

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class ReadContent(Tool):
    name = 'read_content'
    description = "A tool can read content from a file in the TestEdit application."
    inputs = {
        "application_name": {"description": "the application name that need to be opened", "type": "string" }
    }
    output_type = "string"

    def forward(self, application_name):
        apple_script = '''
        tell application "TextEdit"
            set fileContents to {}
            repeat with aDoc in documents
                set docName to name of aDoc
                set docText to text of aDoc
                set end of fileContents to {docName, docText}
            end repeat
            return fileContents
        end tell
        '''

        # 执行 AppleScript 并获取输出
        result = subprocess.run(["osascript", "-e", apple_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            content = result.stdout.strip()
            return (f"Extracted content: {content}")
        else:
            return("Failed in content extraction")
