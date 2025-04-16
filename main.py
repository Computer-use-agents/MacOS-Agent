import argparse
import sys
sys.path.append('.')
from macosagent.macosagent import create_agent
from dotenv import load_dotenv
load_dotenv()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt", 
 
        default="Search for information about NeurIPS 2025, extract key event details (date, location, submission deadline), save it in a structured Excel spreadsheet at /Users/pengxiang/Documents/Code/MacOS-Agent/data/NeurIPS2025_Details.xlsx, and add the submission deadline to the calendar..")
    args = parser.parse_args()
    agent = create_agent()
    result = agent.run(args.prompt)
    print("Agent Response:", result)

if __name__ == "__main__":
    main()