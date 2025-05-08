from macosagent.agents.finder_agent.finder_agent.agents.finder import create_agent

react_agent = create_agent()

instruction= "Copy '/Users/jinchen/Desktop/Finder-Agent/finder_agent/save/a.txt' into '/Users/jinchen/Desktop/Finder-Agent/finder_agent/save/new', and rename it as 'b.txt'."
# instruction= "Copy '/Users/jinchen/Desktop/Finder-Agent/finder_agent/save/a.txt' into clipboard."
# instruction= "Delete the folder '/Users/jinchen/Desktop/Finder-Agent/finder_agent/save/new'."

react_agent.run(instruction)