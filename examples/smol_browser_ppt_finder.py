import argparse
import sys
sys.path.append('.')
from macosagent.macosagent import create_agent
# from dotenv import load_dotenv
import weave
# load the environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

weave.init("Macosagent")
@weave.op()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt", 
 
        default="Search for Trump's assassination, save the assassination picture to './cache/trump.png', create a ppt with the picture and news to './cache/trump.pptx', and finally move the generated ppt to './data'.",
        help="Instructions that you want agent to execute.")
    args = parser.parse_args()
    agent = create_agent()
    result = agent.run(args.prompt)
    # agent.save_trajectory()
    print("Agent Response:", result)

if __name__ == "__main__":
    main()

    # 

    # Create a txt document and write 'Hello World' in it. I want you to save it at './cache/hello.txt' then use finder to move the saved file to './data'.