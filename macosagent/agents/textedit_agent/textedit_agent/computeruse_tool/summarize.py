import base64
import subprocess
import os

from openai import AzureOpenAI
from smolagents import Tool
from dotenv import load_dotenv
from smolagents import AzureOpenAIServerModel
from smolagents import OpenAIServerModel
from importlib.resources import files
from pathlib import Path

from macosagent.llm import create_smol_llm_client

# 加载 .env 文件
# load_dotenv()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class Summarizer(Tool):
    name = 'summarizer'
    description = "Given a GUI task, a tool can summarize what has been doen and what needs to be done."
    inputs = {
        "task": {"description": "instruction of a GUI task", "type": "string" }
    }
    output_type = "string"

    # if os.environ.get("API_SERVER_TYPE") == "AZURE":
    #     model = AzureOpenAIServerModel(
    #         model_id=os.environ.get("AZURE_MODEL"),
    #         azure_endpoint=os.environ.get("AZURE_ENDPOINT"),
    #         api_key=os.environ.get("AZURE_API_KEY"),
    #         api_version=os.environ.get("AZURE_API_VERSION"),
    #     )
    # elif os.environ.get("API_SERVER_TYPE") == "OPENAI":
    #     model = OpenAIServerModel(
    #         model_id=os.environ.get("MODEL"),
    #         api_base=os.environ.get("API_BASE"), 
    #         api_key=os.environ.get("API_KEY"),
    #     )
    # else:
    #     raise ValueError("Invalid API server type. Please check your .env file and ensure API_SERVER_TYPE is set to either 'AZURE' or 'OPENAI'.")

    model = create_smol_llm_client()



    SYSTEM_PROMPT = """You are an AI agent designed to automate GUI tasks. Your goal is to decompose and analyze the task.
    You will be given a task instruction and the current screenshot.
    Please output the subgoals that have been done and subgoals that need to be done.
    Please note that, in this task, we prefer not to use save as, but to directly open the target file and use save. Please judge whether the file has been saved according to the status on the file column.

    # Output Format
    Subgoals have been done: <Based on the current screenshot, please analyze what has been done.>
    Subgoals need to be done: <Based on the current screenshot, please analyze what need to be done.>
    Next goal: <What should do in the next step.>
    """

    def forward(self, task):

        # screenshot_folder_path=str(files("textedit_agent").joinpath("screenshot"))
        screenshot_folder_path = str(Path('macosagent/agents/textedit_agent/textedit_agent').joinpath("screenshot"))

        if not Path(screenshot_folder_path).exists():
            Path(screenshot_folder_path).mkdir(parents=True, exist_ok=True)

        # screenshot_path=str(files("textedit_agent.screenshot").joinpath("screenshot.png"))
        screenshot_path = str(Path('macosagent/agents/textedit_agent/textedit_agent/screenshot').joinpath("screenshot.pn"))

        subprocess.run(["screencapture", screenshot_path])
        SYSTEM_PROMPT=self.SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": task},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(screenshot_path)}"}}
            ]},
        ]

        response = self.model(
            messages=messages,
            max_tokens=1024,
            temperature=1.0
        )
        content = response.content

        return content
