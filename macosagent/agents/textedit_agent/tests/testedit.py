import os

from dotenv import load_dotenv

from macosagent.agents.textedit_agent.textedit_agent.agents.textedit_use import create_agent

# 加载 .env 文件
load_dotenv('/Users/jinchen/Desktop/TextEdit-Agent/.env')

react_agent = create_agent()

# instruction= "Open '/Users/jinchen/Desktop/computer-use-agent/save/a.txt' via TextEdit, add a story about the basketball game, and save it."
# instruction= "Open '/Users/jinchen/Desktop/TextEdit-Agent/save/a.txt' via TextEdit, extract its content."
instruction= "Open '/Users/jinchen/Desktop/TextEdit-Agent/save/b.txt' via TextEdit, write a short story about a basketball game, and save it."

react_agent.run(instruction)