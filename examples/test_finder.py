from finder_agent import FinderAgent


instructions = "Move './data/text.pdf' to './cache'."
agent = FinderAgent()
result = agent.forward(instructions)
print("Operation Result:", result)


