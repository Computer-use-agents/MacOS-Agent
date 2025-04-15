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
 
        default="Search for the date of Stefanie Sun's most recent concert and add a calendar reminder for me to attend on that day.",
        help="Instructions that you want agent to execute.")
    args = parser.parse_args()
    agent = create_agent()
    result = agent.run(args.prompt)
    print("Agent Response:", result)

if __name__ == "__main__":
    main()