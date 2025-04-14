
from powerpoint_agent import PowerPointAgent 
instructions =  "Create a new PowerPoint presentation and add a slide with 'Hello World' in it. I want you to save it at './cache/hello.pptx.' "
agent = PowerPointAgent()
result = agent.forward(instructions)
print(result)