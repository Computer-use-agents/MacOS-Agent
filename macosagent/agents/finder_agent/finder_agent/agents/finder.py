import os
from pathlib import Path

from macosagent.agents.finder_agent.finder_agent.computeruse_tool.tool_box import get_visual_model_tool_box_for_computeruse

from smolagents import AzureOpenAIServerModel
from smolagents import OpenAIServerModel
from smolagents import CodeAgent
import yaml
from importlib.resources import files

from macosagent.llm import create_smol_llm_client

def create_agent() :
    tool_boxes = get_visual_model_tool_box_for_computeruse()

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

    prompt_path = str(Path('macosagent/agents/finder_agent/finder_agent').joinpath("prompt.yaml"))
    # with open(str(files("finder_agent").joinpath("prompt.yaml"))) as file:    
    with open(prompt_path) as file:    
        prompt = yaml.safe_load(file)

    react_agent = CodeAgent(tools=tool_boxes, model=model, prompt_templates = prompt,
            additional_authorized_imports=[
            "requests",
            "zipfile",
            "os",
            "pandas",
            "numpy",
            "sympy",
            "json",
            "bs4",
            "pubchempy",
            "xml",
            "yahoo_finance",
            "Bio",
            "sklearn",
            "scipy",
            "pydub",
            "io",
            "PIL",
            "chess",
            "PyPDF2",
            "pptx",
            "torch",
            "datetime",
            "csv",
            "fractions",
            "matplotlib",
            "pickle",
            "cv2",
            "time"
        ]
    )

    return react_agent

