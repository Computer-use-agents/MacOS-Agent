import os
from smolagents import AzureOpenAIServerModel
from smolagents import CodeAgent
import sys
# set '.' to the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from appagent_box import get_app_agent_box
import yaml
from importlib.resources import files

 



def create_agent():

    # Initialize the agent with the model and tools

    llm_engine = AzureOpenAIServerModel(
        model_id = os.environ.get("AZURE_OPENAI_MODEL"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("OPENAI_API_VERSION")    
    )
    APPAGENT_BOX = get_app_agent_box()
    with open(str(files("macosagent").joinpath("prompt.yaml"))) as file:    
        prompt = yaml.safe_load(file)
    macosagent = CodeAgent(tools=APPAGENT_BOX, model=llm_engine, prompt_templates = prompt)

    return macosagent
