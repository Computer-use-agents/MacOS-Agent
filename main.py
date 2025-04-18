"""Main entry point for the MacOS Agent application.

This module initializes the OpenTelemetry instrumentation and runs the agent
with the provided prompt.
"""

import argparse
import sys
from typing import Any

from dotenv import load_dotenv
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from phoenix.otel import register

# Add current directory to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

# Initialize OpenTelemetry instrumentation
register()
SmolagentsInstrumentor().instrument()

from macosagent.macosagent import create_agent


def main() -> None:
    """Run the MacOS Agent with the provided prompt.
    
    This function:
    1. Parses command line arguments
    2. Creates an agent instance
    3. Runs the agent with the provided prompt
    4. Prints the result
    """
    parser = argparse.ArgumentParser(
        description="Run the MacOS Agent with a specified prompt"
    )
    parser.add_argument(
        "--prompt",
        default="Write 'hello world' it to './result/hello.txt' via TextEdit",
        help="The prompt to execute with the agent"
    )
    args: argparse.Namespace = parser.parse_args()
    agent = create_agent()
    result: Any = agent.run(args.prompt)
    print("Agent Response:", result)


if __name__ == "__main__":
    main()
    