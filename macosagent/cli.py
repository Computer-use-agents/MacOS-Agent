import json
import logging
import uuid
from pathlib import Path

import click
import dotenv

from macosagent.llm.tracing import trace_with_metadata
from macosagent.macosagent import create_agent

logger = logging.getLogger(__name__)


def setup_logging(log_level: str, log_dir: str = None):
    """Configure logging with the specified level and directory."""
    # Set root logger level
    logging.getLogger().setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    # Setup file handler if log_dir is provided
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / "macosagent.log")
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)


def common_options(f):
    """Common options for all commands."""
    f = click.option(
        "--log-level",
        default="DEBUG",
        type=click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
        ),
        help="Set the logging level",
    )(f)
    f = click.option("--log-dir", default="logs")(f)
    f = click.option("--run-id", default=str(uuid.uuid4()))(f)
    return f


@click.group()
def cli():
    dotenv.load_dotenv()


@cli.command("run")
@common_options
@click.option("--task", required=True, help="The task to run")
def start(
    log_level,
    log_dir,
    run_id,
    task,
):
    setup_logging(log_level, log_dir)
    logger.info(f"Starting MacOS Agent {run_id}; {task}")
    @trace_with_metadata(custom_id=run_id, name="macosagent")
    def run_agent(task):
        agent = create_agent()
        result = agent.run(task)
        logger.info(f"MacOS Agent {run_id} finished with result: {result}")
    run_agent(task)


@cli.command("execute")
@common_options
@click.argument("file_path", type=click.Path(exists=True))
def execute(
    file_path,
    log_level,
    log_dir,
    run_id,
):
    """Execute tasks from a file."""
    setup_logging(log_level, log_dir)
    logger.info(f"Starting MacOS Agent {run_id} with file: {file_path}")
    with open(file_path) as f:
        json_data = json.load(f)
    task = json_data["task"]
    @trace_with_metadata(custom_id=run_id, name="macosagent")
    def run_agent(task):
        agent = create_agent()
        result = agent.run(task)
        logger.info(f"MacOS Agent {run_id} finished with result: {result}")
    run_agent(task)

