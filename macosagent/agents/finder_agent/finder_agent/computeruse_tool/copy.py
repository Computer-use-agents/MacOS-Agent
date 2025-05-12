from smolagents import Tool
import os 
from AppKit import NSPasteboard, NSURL

class Copy(Tool):
    name = 'copy_finder'
    description = "A tool can put file or folder into the clipboard in the finder."
    inputs = {
        "file_path": {"description": "the file or folder path that need to be copyed", "type": "string"}
    }
    output_type = "string"

    def forward(self, file_path):

        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        try:
            # 确保路径存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"路径不存在: {file_path}")
            
            # 创建 NSURL 对象
            file_url = NSURL.fileURLWithPath_(file_path)
            
            # 获取通用剪贴板
            pb = NSPasteboard.generalPasteboard()
            
            # 清除剪贴板当前内容
            pb.clearContents()
            
            # 写入文件URL到剪贴板
            result = pb.writeObjects_([file_url])
            return "Copy the folder or file with no explicit errors."
        except:
            return "Some errors are occurred in copying the folder or file."