import asyncio
import base64
import json
import logging
import os
import time
from datetime import datetime
from io import BytesIO
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from PIL import Image
from smolagents import AgentError, MessageRole, Tool, ToolCallingAgent

from macosagent.agents.word_agent.agent.prompt import SYSTEM_PROMPT
from macosagent.agents.word_agent.agent.views import (
    ActionModel,
    ActionResult,
    AgentOutput,
)
from macosagent.agents.word_agent.word import Word, WordConfig
from macosagent.agents.word_agent.word.context import WordContext
from macosagent.llm import LLMEngine, create_langchain_llm_client
from macosagent.llm.tracing import trace_with_metadata

logger = logging.getLogger(__name__)


def log_response(response: AgentOutput) -> None:
    """Utility function to log the model's response."""

    if "Success" in response.current_state.evaluation_previous_goal:
        emoji = "👍"
    elif "Failed" in response.current_state.evaluation_previous_goal:
        emoji = "⚠"
    else:
        emoji = "🤷"

    logger.info(f"{emoji} Eval: {response.current_state.evaluation_previous_goal}")
    logger.info(f"🧠 Memory: {response.current_state.memory}")
    logger.info(f"🎯 Next goal: {response.current_state.next_goal}")
    for i, action in enumerate(response.action):
        logger.info(
            f"🛠️  Action {i + 1}/{len(response.action)}: {action.model_dump_json(exclude_unset=True)}"
        )


class ReactJsonAgent(ToolCallingAgent):
    """
    This agent that solves the given task step by step, using the ReAct framework:
    While the objective is not reached, the agent will perform a cycle of thinking and acting.
    The tool calls will be formulated by the LLM in JSON format, then parsed and executed.
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        system_prompt: str | None = SYSTEM_PROMPT,
        controller=None,
        max_iterations: int = 6,
        **kwargs,
    ):
        self.llm = llm
        # Initialize the controller
        if controller is None:
            from macosagent.agents.word_agent.controller import Controller

            self.controller = Controller()
        else:
            self.controller = controller
        self.system_prompt = system_prompt
        self.word = Word(WordConfig())
        self.word_context = WordContext(
            word=self.word,
        )

        self.history = []
        self.tool_call_method = "function_calling"
        self.save_conversation_path = "./results"
        os.makedirs(self.save_conversation_path, exist_ok=True)
        self.llm_engine = LLMEngine(self.llm, self._get_model_name())
        self.planning_interval = None
        self.plan_type = None
        self.max_iterations = max_iterations

    def _get_model_name(self):
        if hasattr(self.llm, "model_name"):
            return self.llm.model_name
        elif hasattr(self.llm, "model"):
            return self.llm.model
        else:
            return self.llm.model_id

    def get_prompt(
        self,
        task: str,
        image: Image.Image | None = None,
        interactive_elements_prompt: str | None = None,
        interactive_elements: list[dict] | None = None,
        max_steps: int = 100,
        current_step: int = 0,
    ):
        tool_call_example = [
            {
                "name": "AgentOutput",
                "args": {
                    "current_state": {
                        "evaluation_previous_goal": "Success - I opend the calender",
                        "memory": "Starting with the new task. I have completed 1/10 steps",
                        "next_goal": "Left single click on the date",
                    },
                    "action": [{"left_single_click": {"index": 0}}],
                },
                "id": str(1),
                "type": "tool_call",
            }
        ]
        context = (
            "\n\nAvailable actions:\n"
            + self.controller.registry.get_prompt_description()
        )
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content="Context for the task" + context),
            HumanMessage(content=[{"type": "text", "text": "Task: " + task}]),
            HumanMessage(content="Example output:"),
            AIMessage(content="", tool_calls=tool_call_example),
            ToolMessage(content="Click success!", tool_call_id="1"),
            HumanMessage(content="[Your task history memory starts here]"),
        ]

        for h in self.history:
            messages.append(AIMessage(content="", tool_calls=h["tool_calls"]))
            messages.append(
                ToolMessage(content="", tool_call_id=h["tool_calls"][0]["id"])
            )
            for obs in h["observation"]:
                messages.append(HumanMessage(content=obs))
        if interactive_elements_prompt is None:
            interactive_elements_prompt = (
                "No interactive elements found, since the app is not open yet."
            )
        current_state = HumanMessage(
            content=[
                {"type": "text", "text": "[Task history ends here]"},
                {
                    "type": "text",
                    "text": f"[Current state starts here]\nThe following is one-time information - if you need to remember it write it to memory:\nInteractive elements from top layer of the current page inside the viewport:\n{interactive_elements_prompt}\nCurrent step: {current_step}/{max_steps}\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
                },
            ]
        )
        if image is not None:
            messages.append(
                HumanMessage(
                    content=[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/png;base64,"
                                + self.image_to_base64(image)
                            },
                        }
                    ]
                )
            )
        messages.append(current_state)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(
            os.path.join(
                self.save_conversation_path, f"conversation_{current_time}.txt"
            ),
            "w",
        ) as f:
            _write_messages_to_file(f, messages)
            if image is not None:
                image.save(
                    os.path.join(
                        self.save_conversation_path, f"screenshot_{current_time}.png"
                    )
                )
        with open(
            os.path.join(
                self.save_conversation_path, f"accessibility_tree_{current_time}.json"
            ),
            "w",
        ) as f:
            json.dump(interactive_elements, f, indent=2, ensure_ascii=False)

        return messages

    def step(self, log_entry: dict[str, Any]):
        """
        Perform one step in the ReAct framework: the agent thinks, acts, and observes the result.
        The errors are raised here, they are caught and logged in the run() method.
        """
        response = self.get_next_action(log_entry)
        logger.info(f"Response: {response}")
        agent_output = response["parsed"]
        action = agent_output.action
        log_response(agent_output)
        results = asyncio.run(self.multi_act(action))
        logger.info(f"Results: {results}")
        self._make_history(response["raw"], results)
        return results

    def get_next_action(self, log_entry: dict[str, Any]) -> dict[str, Any]:
        task = log_entry.get("task", "")
        if len(task) == 0:
            task = self.task

        max_steps = log_entry.get("max_steps", 100)
        current_step = log_entry.get("current_step", 0)
        try:
            state = self.word_context.get_state()
            image = state.screenshots_som[0]
            interactive_elements_prompt, interactive_elements = (
                self.word_context.get_accessibility_tree_prompt()
            )
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            image = None
            interactive_elements_prompt = None
            interactive_elements = None
        prompt = self.get_prompt(
            task,
            image,
            interactive_elements_prompt,
            interactive_elements,
            max_steps,
            current_step,
        )
        action_model = self.controller.registry.create_action_model()
        # Create output model with the dynamic actions
        agent_output_model = AgentOutput.type_with_custom_actions(action_model)
        structured_llm = self.llm.with_structured_output(
            agent_output_model, include_raw=True, method=self.tool_call_method
        )
        response = structured_llm.invoke(prompt)
        return response

    def image_to_base64(self, image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    async def multi_act(self, actions: list[ActionModel]) -> list[ActionResult]:
        results = []
        for i, action in enumerate(actions):
            logger.debug(f"Executed action {i + 1} / {len(actions)}")
            result = await self.controller.act(
                action,
                self.word_context,
            )
            results.append(result)
            logger.debug(f"Action {i + 1} / {len(actions)} executed")
        return results

    def _make_history(self, raw_response: AIMessage, results: list[ActionResult]):
        history_item = {
            "tool_calls": raw_response.tool_calls,
        }
        observation = []
        for result in results:
            if result.include_in_memory:
                if result.extracted_content:
                    observation.append(
                        "Action result: " + str(result.extracted_content)
                    )

                if result.error:
                    observation.append("Action error: " + result.error)

        history_item["observation"] = observation
        self.history.append(history_item)

    def direct_run(self, task: str):
        """
        Runs the agent in direct mode, returning outputs only at the end: should be launched only in the `run` method.
        """
        iteration = 0
        while iteration < self.max_iterations:
            logger.info(f"Iteration {iteration} / {self.max_iterations}")
            step_start_time = time.time()
            step_log_entry = {"iteration": iteration, "start_time": step_start_time}
            try:
                if (
                    self.planning_interval is not None
                    and iteration % self.planning_interval == 0
                ):
                    self.planning_step(
                        task, is_first_step=(iteration == 0), iteration=iteration
                    )
                results = self.step(step_log_entry)
                is_done = False
                for result in results:
                    is_done = result.is_done
                    if is_done:
                        break

                if is_done:
                    break

            except AgentError as e:
                self.logger.error(e, exc_info=1)
                step_log_entry["error"] = e
            finally:
                step_end_time = time.time()
                step_log_entry["step_end_time"] = step_end_time
                step_log_entry["step_duration"] = step_end_time - step_start_time
                iteration += 1

        return self.provide_final_answer(task)
        # return final_answer

    def run(self, task: str, stream: bool = False, reset: bool = True, **kwargs):
        """
        Runs the agent for the given task.

        Args:
                task (`str`): The task to perform

        Example:
        ```py

        agent = ReactCodeAgent(tools=[])
        agent.run("What is the result of 2 power 3.7384?")
        ```
        """
        self.task = task
        return self.direct_run(task)

    def provide_final_answer(self, task, success: bool = True) -> str:
        """
        This method provides a final answer to the task, based on the logs of the agent's interactions.
        """
        if not success:
            self.prompt = [
                {
                    "role": MessageRole.SYSTEM,
                    "content": "An agent tried to answer an user query but it got stuck and failed to do so. You are tasked with providing an answer instead. Here is the agent's memory:",
                }
            ]
        else:
            self.prompt = [
                {
                    "role": MessageRole.SYSTEM,
                    "content": "An agent tried to answer an user query and finished successfully. Here is the agent's memory:",
                }
            ]
        # self.prompt += self.write_inner_memory_from_logs()[1:]
        for h in self.history:
            self.prompt.append(
                {
                    "role": MessageRole.USER,
                    "content": "Agent is using the following tool calls:"
                    + json.dumps(h["tool_calls"], indent=4, ensure_ascii=False),
                }
            )
            obs = ""
            for obs in h["observation"]:
                obs += obs + "\n"
            self.prompt.append(
                {"role": MessageRole.ASSISTANT, "content": "Observation:\n" + obs}
            )

        self.prompt += [
            {
                "role": MessageRole.USER,
                "content": f"Based on the above, please provide an answer to the following user request:\n{task}",
            }
        ]

        logger.info("Curent Prompt: %s" % self.prompt)
        try:
            return self.llm_engine(self.prompt)
        except Exception as e:
            return f"Error in generating final llm output: {e}."


def _write_messages_to_file(f: Any, messages: list[BaseMessage]) -> None:
    """Write messages to conversation file"""
    for message in messages:
        f.write(f" {message.__class__.__name__} \n")

        if isinstance(message.content, list):
            for item in message.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    f.write(item["text"].strip() + "\n")
        elif isinstance(message.content, str):
            if len(message.content) > 0:
                try:
                    content = json.loads(message.content)
                    f.write(json.dumps(content, indent=2) + "\n")
                except json.JSONDecodeError:
                    f.write(message.content.strip() + "\n")
            if (
                hasattr(message, "tool_calls")
                and message.tool_calls is not None
                and len(message.tool_calls) > 0
            ):
                tool_calls = message.tool_calls
                f.write(json.dumps(tool_calls, indent=2) + "\n")
            if (
                hasattr(message, "tool_call_id")
                and message.tool_call_id is not None
                and len(message.tool_call_id) > 0
            ):
                f.write(f"Tool call id: {message.tool_call_id}\n")

        f.write("\n")




class WordAgent(Tool):
    name = "word_agent"
    description = "The Word-Agent is designed to perform a variety of tasks related to Microsoft Word documents. It can handle basic operations such as opening, saving, and closing documents, as well as more complex tasks like inserting images, tables, and text, and modifying document styles. Additionally, it can delete content and interact with elements using PyAutoGUI."
    inputs = {  # noqa: RUF012
        "instruction": {
            "description": "an instruction of a calendar app agent",
            "type": "string",
        },
    }
    output_type = "string"

    @trace_with_metadata(observation_name="word_agent", tags=["word_agent"])
    def forward(self, instruction: str) -> str:
        logger.info(f"WordAgent instruction: {instruction}")
        llm = create_langchain_llm_client()
        agent = ReactJsonAgent(
            llm=llm,
            max_iterations=20
        )
        result = agent.run(instruction)
        return result
        # result = asyncio.run(agent.run(max_steps=30))
        # logger.info(f"WordAgent result: {result.extracted_content}")
        # return f"Execution result: {result.extracted_content}"

        # agent = ReactJsonAgent(llm=llm, max_iterations=10)
        # result = self.agent.run(instruction)
        # # print(result)
        # return f"Execution result: {result}"
