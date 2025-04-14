
from excel_agent import ExcelAgent
instructions =  "Create a new Excel file and write 'Hello World' in it. I want you to save it at './cache/hello.xlsx.' "
agent = ExcelAgent()
result = agent.forward(instructions)
print(result)