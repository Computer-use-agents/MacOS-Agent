from AppKit import NSPasteboard, NSURL

file_path = "./data/poem.txt"
# 创建 NSURL 对象
file_url = NSURL.fileURLWithPath_(file_path)

# 获取通用剪贴板
pb = NSPasteboard.generalPasteboard()

# 清除剪贴板当前内容
pb.clearContents()

result = pb.writeObjects_([file_url])