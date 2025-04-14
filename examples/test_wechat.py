
from wechat_agent import WechatAgent
instructions =  "Send a WeChat message to 'Kendrick Stein' saying 'Hello, how are you?'"
agent = WechatAgent()
result = agent.forward(instructions)
print("Result:", result)