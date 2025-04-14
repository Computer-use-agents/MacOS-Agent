 # task = "打开data/text.pdf, 找到 "Fire: A dataset for feedback integration and refinement evaluation of multimodal models" 发表的年份，在日历中查看那年10月31日我在干嘛？"


import sys
import os
# set '.' to the current directory
sys.path.append('.')

import argparse
from macosagent.macosagent import create_agent
from dotenv import load_dotenv

# load the environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt", 
        default="Open data/text.pdf with Preview, Search for the keyword 'Fire' and find the year when it was published, and check the calendar to see what I was doing on October 31st of that year.",
        help="Instructions that you want agent to execute.")
    args = parser.parse_args()
    agent = create_agent()
    result = agent.run(args.prompt)
    agent.save_trajectory()
    print("Agent Response:", result)

if __name__ == "__main__":
    main()