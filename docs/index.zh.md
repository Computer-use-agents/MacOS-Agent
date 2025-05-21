# MacOS 代理
## 安装指南

### 1. 安装 Python 依赖

请遵循 [uv 文档](https://docs.astral.sh/uv/reference/cli/#uv)中的说明来安装 uv。

### 2. 克隆并设置仓库

```bash
# 克隆仓库
git clone https://github.com/yourusername/MacOS-Agent.git
cd MacOS-Agent

# 安装项目依赖
uv sync
```

### 3. 安装 Playwright

```bash
# 安装 Playwright 用于网页自动化
npm init playwright@latest
```

### 4. 配置辅助功能权限

为了启用系统自动化，您需要授予辅助功能权限：

1. 打开 系统设置 > 隐私与安全 > 辅助功能
2. 点击 “+” 按钮添加您的代码编辑器
3. 导航至 应用程序 并选择您的编辑器
4. 勾选复选框以启用权限

<div style="display: flex; justify-content: space-between;">
    <img src="assets/acc_tree1.png" alt="辅助功能树权限1" width="32%">
    <img src="assets/acc_tree2.png" alt="辅助功能树权限2" width="32%">
    <img src="assets/acc_tree3.png" alt="辅助功能树权限3" width="32%">
</div>

## 使用方法

### 执行代理

使用 uv 来运行代理
```bash
uv sync
uv run macosagent execute examples/tasks/task1.json
```
请查看 `examples/tasks/task1.json` 获取示例任务。以下是一个示例任务：
```json
{
  "task": "一个任务指令'",
}
```


## 开发设置

### Pre-commit 钩子

本项目使用 pre-commit 钩子以确保每次提交前的代码质量。设置包括：

1. **ruff**: 一个快速的 Python linter 和格式化工具
2. **pylint**: 一个全面的 Python 代码分析器

#### 配置文件

- `.pre-commit-config.yaml`: 定义 pre-commit 钩子及其配置
- `ruff.toml`: 配置 ruff linting 规则
- `pylintrc`: 配置 pylint 分析规则

#### 设置流程

1. 使用 uv 安装 pre-commit:
   ```bash
   uv pip install pre-commit
   ```

2. 安装 git 钩子:
   ```bash
   pre-commit install
   ```

3. 手动对所有文件运行检查:
   ```bash
   pre-commit run --all-files
   ```
4. 当您执行 git commit 时，pre-commit 钩子将自动运行。如果您想跳过钩子，可以使用 `git commit --no-verify`。

#### 自定义

- ruff 被配置为自动 