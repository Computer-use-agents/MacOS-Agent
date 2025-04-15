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
 
        default="Use QuickTimePlayer to cut the video '/Users/pengxiang/Documents/Code/MacOS-Agent/data/test.mov' to only save the last 3 seconds. Also, could you identify where this video is taken and look up the most famous attractions in that place and compile them into an Excel table '/Users/pengxiang/Documents/Code/MacOS-Agent/data/Attractions.xlsx'?",
        help="Instructions that you want agent to execute.")
    args = parser.parse_args()
    agent = create_agent()
    result = agent.run(args.prompt)
    print("Agent Response:", result)

if __name__ == "__main__":
    main()