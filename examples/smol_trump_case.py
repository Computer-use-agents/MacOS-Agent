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
 
        default="Search for news about Trump's assassination in Florida on Wikipedia, and insert it into the local word file './cache/2024TrumpAssassination.docx' Chapter 3")
    args = parser.parse_args()
    agent = create_agent()
    result = agent.run(args.prompt)
    # agent.save_trajectory()
    print("Agent Response:", result)

if __name__ == "__main__":
    main()

 