from textedit_agent import TextEditAgent

instructions = "Create a txt document and write 'Hello World' in it. I want you to save it at ./cache/hello.txt"
agent = TextEditAgent()
result = agent.forward(instructions)
print(result)