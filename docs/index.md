# MacOS Agent
## Development Setup

### Executing the agent

use uv to run the agent
```bash
uv sync
uv run macosagent execute examples/task1.json
```
Checkout `examples/task1.json` for an example task.

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality before each commit. The setup includes:

1. **ruff**: A fast Python linter and formatter
2. **pylint**: A comprehensive Python code analyzer

#### Configuration Files

- `.pre-commit-config.yaml`: Defines the pre-commit hooks and their configurations
- `ruff.toml`: Configures ruff linting rules
- `pylintrc`: Configures pylint analysis rules

#### Setup Process

1. Install pre-commit using uv:
   ```bash
   uv pip install pre-commit
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

3. Run checks manually on all files:
   ```bash
   pre-commit run --all-files
   ```
4. When you do git commit, the pre-commit hooks will run automatically. If you want to skip the hooks, you can use `git commit --no-verify`.
#### Customization

- ruff is configured to auto