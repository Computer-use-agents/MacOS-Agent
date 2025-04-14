# MacOS Agent

[//]: # (Optional: Add a brief one-sentence description of the agent here)

This document provides instructions on how to set up, install dependencies for, and run the MacOS Agent using `uv`, the fast Python package installer and resolver.

## Prerequisites

*   **macOS**: This setup guide is specific to macOS.
*   **Python 3.11**: This project requires Python version 3.11. Ensure it's installed and accessible in your PATH. You can check your version with `python3 --version`. Consider using `pyenv` or the official Python installer for macOS.
*   **uv**: The `uv` tool is required for environment and package management.
*   **Git**: Needed to clone the repository (usually pre-installed on macOS or available via Xcode Command Line Tools).

## Installation

Follow these steps to get the agent running on your Mac:

1.  **Install uv**:
    If you don't have `uv` installed, use one of the following methods:

    *   Using `pip` (if you have another Python environment active):
        ```bash
        pip install uv
        ```
    *   Using `curl`:
        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```
    Verify the installation:
    ```bash
    uv --version
    ```

2.  **Clone the Repository**:
    Get the project code using Terminal:
    ```bash
    git clone <repository-url> # Replace <repository-url> with the actual URL
    cd MacOS-Agent             # Navigate into the project directory
    ```

3.  **Create a Virtual Environment**:
    Use `uv` to create a dedicated virtual environment using Python 3.11:
    ```bash
    uv venv --python 3.11 .venv
    ```
    This command creates a directory named `.venv`. If `uv` cannot find a Python 3.11 installation, ensure it's installed and available in your system's PATH.

4.  **Activate the Virtual Environment**:
    Before installing dependencies or running the agent, activate the environment in your Terminal:
    ```bash
    source .venv/bin/activate
    ```
    Your shell prompt should change to indicate the active environment (e.g., `(.venv) ...`).

5.  **Install Dependencies**:
    Install the required packages using `uv`, depending on how the project's dependencies are defined:

    *   **Method 1: Using `uv add`**
        
        ```bash
        uv add "word-agent @ git+https://github.com/Computer-use-agents/Word-Agent.git"
        uv add "wechat-agent @ git+https://github.com/Computer-use-agents/Wechat-Agent.git"
        uv add "finder-agent @ git+https://github.com/Computer-use-agents/Finder-Agent.git"
        uv add "calendar-agent @ git+https://github.com/Computer-use-agents/Calendar-Agent.git"
        uv add "player-agent @ git+https://github.com/Computer-use-agents/QuickTime-Agent.git"
        uv add "powerpoint-agent @ git+https://github.com/Computer-use-agents/PowerPoint-Agent.git"
        uv add "excel-agent @ git+https://github.com/Computer-use-agents/Excel-Agent.git"
        uv add "preview-agent @ git+https://github.com/Computer-use-agents/Preview-Agent.git"
        uv add "browser-agent @ git+https://github.com/Computer-use-agents/Browser-Agent.git"
        ```
    *   **Method 2: Using `requirements.txt`**
        If the project uses a `requirements.txt` file:
        ```bash
        uv pip install -r requirements.txt
        ```
        *(Replace `requirements.txt` if your file has a different name)*



    *   **Note on `uv add`**: The `uv add <package-name>` command is used to *add* a new dependency to your `pyproject.toml` file and install it. It's not typically used for installing all dependencies from a pre-existing list like `requirements.txt`.

## Running the Agent

Once the setup is complete and the virtual environment is active, run the agent from your Terminal:

```bash
python3 main.py # Replace with the actual command to start the agent
```

*(Ensure you replace `<repository-url>` and the agent execution command with the correct values for this project.)*