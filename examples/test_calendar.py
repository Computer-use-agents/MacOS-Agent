
from calendar_agent import CalendarAgent 
instructions =  "Create a new calendar event on 2025-05-01 at 10:00 AM and set the title to 'Meeting with Bob'."
agent = CalendarAgent()
result = agent.forward(instructions)
print(result)