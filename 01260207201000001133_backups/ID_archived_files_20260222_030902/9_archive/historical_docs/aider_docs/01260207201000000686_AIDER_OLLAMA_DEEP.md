  Windows

  - Ollama 0.12.11 - Running and serving API at
  http://127.0.0.1:11434
  - Models installed:
    - qwen2.5-coder:7b (7.6B params, 4.7GB)
    - deepseek-coder:latest (1B params, 776MB)
    - deepseek-r1:latest (8.2B params, 5.2GB)
    - deepcoder:14b (14.8B params, 9GB)

  WSL (Ubuntu)

  - Python 3.12.3
  - pip 24.0
  - git 2.43.0
  - pipx (for Python app management)
  - aider-chat 0.86.1 (was already installed)

  What Was Installed

  - ollama-code-cli 1.0.3 - Installed via pipx

  What Was Configured

  ~/.bashrc (WSL)

  - Set OLLAMA_API_BASE="http://127.0.0.1:11434"
  - Removed conflicting old entries
  - Added shell aliases:
    - aider-qwen, aider-ds, aider-r1, aider-dc14
    - oc-qwen, oc-deepseek, oc-r1

  ~/.aider.conf.yml (WSL)

  - Default model: ollama_chat/qwen2.5-coder:7b
  - Editor/weak model configuration
  - Auto-commits enabled

  ~/.aider.model.settings.yml (WSL)

  - Per-model settings for all 4 models
  - num_ctx: 32768 for larger context
  - Diff edit format configured

  Validation Results

  | Component                          | Status |
  |------------------------------------|--------|
  | Ollama API reachable from WSL      | ✅      |
  | Aider connects to Ollama           | ✅      |
  | ollama-code-cli connects to Ollama | ✅      |

  Usage

  From WSL Terminal:

  # Source the updated bashrc
  source ~/.bashrc

  # Use Aider with Qwen (default)
  cd /mnt/c/Users/richg/YourRepo
  aider

  # Or use aliases for specific models
  aider-qwen     # qwen2.5-coder:7b
  aider-ds       # deepseek-coder
  aider-r1       # deepseek-r1 (reasoning)
  aider-dc14     # deepcoder:14b

  # Use ollama-code-cli
  oc-qwen "Explain this code"
  oc-deepseek "Refactor this function"

  From Windows PowerShell:

  # Check Ollama status
  ollama list
  curl http://127.0.0.1:11434/api/tags