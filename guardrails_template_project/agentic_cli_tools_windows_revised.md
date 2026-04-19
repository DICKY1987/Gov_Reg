# Windows-first Agentic CLI Tools Companion Guide (Revised)

- Document ID: DOC-CLI-AGENTS-WIN-001
- Version: 2.0.0
- Last Updated (UTC): 2026-03-27T09:10:04Z
- Status: Updated (Cody→Amp, Plandex Cloud sunset, Windows normalization)
- Audience: Windows-first developers using GitHub Copilot + Claude Code + Codex
- Scope: Aider, Sourcegraph (MCP + src CLI), Amp, Plandex (local/self-hosted)

## 0. What changed in this revision

1. **Removed Cody CLI instructions** (Cody Free/Pro discontinued; Cody CLI is now effectively Enterprise-only).
2. **Added Amp CLI** (Sourcegraph’s agentic replacement).
3. **Added Sourcegraph MCP server** (preferred integration path for whole-codebase search/navigation inside agents).
4. **Updated Aider install details** (pipx Python range; `aider-install` uses `uv` and installs Python 3.12 if needed).
5. **Updated Plandex guidance** (Cloud wind-down; Windows requires WSL; local/self-hosted only for new users).
6. **Normalized all examples to Windows/PowerShell first**, with WSL/Linux as secondary.

---

## 1. Tool roles (use these for the work you actually do)

### 1.1 Aider (git-first refactoring + safe edit audit)
Use Aider when you want **multi-file refactors** with **automatic commits** and **easy rollback**. Aider is strongest when you can keep changes inside a branch and review diffs per commit.

### 1.2 Sourcegraph MCP server (agent wiring for code search/navigation)
Use Sourcegraph MCP when you want your agents (Claude Code, Amp, others) to reliably:
- search across repos,
- read files,
- navigate symbols (definitions/references),
- search commits/diffs.

This is usually the best “whole-codebase context” upgrade.

### 1.3 Sourcegraph `src` CLI (batch search + automation glue)
Use `src` when you want:
- scripted searches returning JSON,
- batch changes / automation via CLI,
- deterministic pipelines that parse results into downstream steps.

### 1.4 Amp CLI (agentic execution in the terminal)
Use Amp as a terminal agent that can plan and execute changes, and connect to IDEs.
If you already rely on Sourcegraph for code intelligence, Amp is the “agentic layer” on top.

### 1.5 Plandex (agentic planning + execution; WSL required on Windows)
Use Plandex for **multi-step plans** that run in a controlled loop (REPL, autonomy modes).
As of late 2025, treat it as **local/self-hosted only** for new users.

---

## 2. Windows baseline requirements (preflight)

### 2.1 Required commands (PowerShell)

```powershell
git --version
python --version
node --version
npm --version
```
- If `git` is missing: install Git for Windows and ensure it is on PATH.
- If `node/npm` is missing: install Node.js (prefer LTS; Amp/Cody tooling expects modern Node).
- If `python` is missing: install Python 3.12+ recommended for tooling compatibility.

### 2.2 WSL (required for Plandex on Windows)

Install WSL (Admin PowerShell):

```powershell
wsl --install
wsl --list --verbose
```

Then open your Linux distro shell and confirm:

```bash
git --version
python3 --version
```

---

## 3. Common configuration conventions (PowerShell-first)

### 3.1 Session env vars (recommended for safety)

```powershell
$env:ANTHROPIC_API_KEY = "<YOUR_KEY>"
$env:OPENAI_API_KEY    = "<YOUR_KEY>"
$env:SRC_ENDPOINT       = "https://sourcegraph.example.com"
$env:SRC_ACCESS_TOKEN   = "<YOUR_SOURCEGRAPH_TOKEN>"
```

### 3.2 Persisting env vars (only if you accept the security tradeoff)

```powershell
setx ANTHROPIC_API_KEY "<YOUR_KEY>"
setx OPENAI_API_KEY "<YOUR_KEY>"
setx SRC_ENDPOINT "https://sourcegraph.example.com"
setx SRC_ACCESS_TOKEN "<YOUR_SOURCEGRAPH_TOKEN>"
```

---

## 4. Aider: install, verify, and workflow wiring

### 4.1 Install Aider (recommended: `aider-install`)

**PowerShell**
```powershell
python -m pip install --upgrade aider-install
aider-install
```

Notes:
- `aider-install` sets up an isolated environment and can install Python 3.12 if needed.
- Aider’s dependencies require Python **3.9–3.12** (pipx installs should use that range).

### 4.2 Verify

```powershell
aider --help
aider --version
```

### 4.3 Minimal project workflow

```powershell
cd C:\Users\<you>\code\myproject
git checkout -b ai/aider-refactor

# Example: run a guided refactor
aider --model sonnet
```

Operational rules:
- Keep the repo clean before running (commit/stash local changes).
- Review commit-by-commit (Aider’s default flow is “edit -> commit”).

---

## 5. Sourcegraph: MCP server (preferred) and src CLI (automation)

### 5.1 Sourcegraph MCP server: connect agents (Amp + Claude Code)

**Server URL pattern**
- Full tools: `https://<INSTANCE>/.api/mcp`
- Deep Search: `https://<INSTANCE>/.api/mcp/deepsearch`

#### 5.1.1 Add MCP server to Amp

```bash
amp mcp add sg https://sourcegraph.example.com/.api/mcp
```

#### 5.1.2 Add MCP server to Claude Code

```bash
claude mcp add --transport http sg https://sourcegraph.example.com/.api/mcp
```

### 5.2 Sourcegraph `src` CLI: install and authenticate

#### 5.2.1 Install (PowerShell)

Option A (npm):
```powershell
npm install -g @sourcegraph/src
```

Option B (Docker, no install):
```powershell
docker run --rm=true sourcegraph/src-cli:latest search "hello world"
```

#### 5.2.2 Configure auth (PowerShell env vars)

```powershell
$env:SRC_ENDPOINT = "https://sourcegraph.example.com"
$env:SRC_ACCESS_TOKEN = "<YOUR_SOURCEGRAPH_TOKEN>"
```

#### 5.2.3 Example: deterministic search output (JSON lines)

```powershell
src search "ALLOCATE_FILE_ID" --json-lines | Out-File -FilePath .\generated\src_search.allocate_file_id.jsonl
```

---

## 6. Amp: install, verify, and wiring

### 6.1 Install Amp

#### 6.1.1 Install via npm (works on Windows)

```powershell
npm install -g @sourcegraph/amp
```

#### 6.1.2 Install via script (macOS/Linux/WSL)

```bash
curl -fsSL https://ampcode.com/install.sh | bash
```

### 6.2 Verify

```powershell
amp --help
```

### 6.3 First run + login

```powershell
amp
```

Follow the browser prompt (or run `amp login` if prompted).

### 6.4 Wire Amp to Sourcegraph MCP (recommended)

```powershell
amp mcp add sg https://sourcegraph.example.com/.api/mcp
```

---

## 7. Plandex: local/self-hosted only (WSL required)

### 7.1 Status and constraints (Windows)

- Plandex Cloud stopped accepting new users; treat cloud as legacy-only.
- **On Windows, Plandex only works correctly inside WSL**.

### 7.2 Install (run in WSL)

```bash
curl -sL https://plandex.ai/install.sh | bash
plandex --help
```

### 7.3 Local Mode Quickstart (Docker-based self-host)

Follow Plandex “Local Mode Quickstart” and run the local server (WSL recommended).

Typical local mode host:
- `http://localhost:8099`

Example provider key (OpenRouter):
```bash
export OPENROUTER_API_KEY="<YOUR_KEY>"
```

### 7.4 Run the REPL in your repo

```bash
cd /mnt/c/Users/<you>/code/myproject
git checkout -b ai/plandex-plan
plandex
```

---

## 8. Deterministic automation spec (tasks your CLI app can run)

This section is a **machine-oriented** task list your automation can implement.
Each task has: purpose, preconditions, commands (PowerShell/WSL), verify, evidence, failure policy.

### TASK: TOOL_AIDER_INSTALL_010

```yaml
task_id: TOOL_AIDER_INSTALL_010
purpose: Install Aider into an isolated environment
platforms: [windows_powershell, wsl_bash]
preconditions:
  - command_exists: python
  - command_exists: git
commands:
  windows_powershell:
    - python -m pip install --upgrade aider-install
    - aider-install
  wsl_bash:
    - python3 -m pip install --upgrade aider-install
    - aider-install
verify:
  - aider --help
evidence:
  - path: generated/evidence/tool_install/aider_install.stdout.txt
  - path: generated/evidence/tool_install/aider_install.stderr.txt
failure:
  on_nonzero_exit: abort
```

### TASK: TOOL_SRC_INSTALL_010

```yaml
task_id: TOOL_SRC_INSTALL_010
purpose: Install Sourcegraph src CLI (npm method)
platforms: [windows_powershell]
preconditions:
  - command_exists: node
  - command_exists: npm
commands:
  windows_powershell:
    - npm install -g @sourcegraph/src
verify:
  - src --help
evidence:
  - path: generated/evidence/tool_install/src_install.stdout.txt
failure:
  on_nonzero_exit: abort
```

### TASK: TOOL_AMP_INSTALL_010

```yaml
task_id: TOOL_AMP_INSTALL_010
purpose: Install Amp CLI (npm method for Windows)
platforms: [windows_powershell]
preconditions:
  - command_exists: node
  - command_exists: npm
commands:
  windows_powershell:
    - npm install -g @sourcegraph/amp
verify:
  - amp --help
evidence:
  - path: generated/evidence/tool_install/amp_install.stdout.txt
failure:
  on_nonzero_exit: abort
```

### TASK: WIRE_SOURCEGRAPH_MCP_010

```yaml
task_id: WIRE_SOURCEGRAPH_MCP_010
purpose: Add Sourcegraph MCP server to Amp and Claude Code
platforms: [wsl_bash, windows_powershell]
inputs:
  sourcegraph_instance_url:
    required: true
    example: https://sourcegraph.example.com
commands:
  wsl_bash:
    - amp mcp add sg {sourcegraph_instance_url}/.api/mcp
    - claude mcp add --transport http sg {sourcegraph_instance_url}/.api/mcp
verify:
  - amp mcp list
  - claude mcp list
evidence:
  - path: generated/evidence/mcp/amp_mcp_list.txt
  - path: generated/evidence/mcp/claude_mcp_list.txt
failure:
  on_nonzero_exit: abort
```

---

## 9. Recommended usage patterns for your project

### Pattern A: “Map files to features” (your current biggest bottleneck)
1. Use Sourcegraph MCP / src search to locate definitions, references, and “where used”.
2. Export results as JSONL evidence.
3. Use Aider to implement targeted refactors or metadata extraction.
4. Use Plandex (WSL) for multi-step migrations where you want a plan + supervised execution loop.

### Pattern B: “Registry automation changes”
- Use Aider for safe multi-file edits + commit trail.
- Use Sourcegraph MCP to find every call site of ID allocation / registry writes.
- Use Plandex when the change set spans many subsystems and you want explicit plan steps.

---

## 10. References (official docs)

- Aider install docs: https://aider.chat/docs/install.html  
- `aider-install` (PyPI): https://pypi.org/project/aider-install/  
- Aider uv installer notes: https://aider.chat/2025/01/15/uv.html  
- Aider release history: https://aider.chat/HISTORY.html  
- Sourcegraph src-cli (GitHub): https://github.com/sourcegraph/src-cli  
- Sourcegraph MCP docs: https://sourcegraph.com/docs/api/mcp  
- Sourcegraph Cody Free/Pro deprecation notice: https://sourcegraph.com/blog/changes-to-cody-free-pro-and-enterprise-starter-plans  
- Amp CLI (npm): https://www.npmjs.com/package/@sourcegraph/amp  
- Amp manual: https://ampcode.com/manual  
- Plandex install docs: https://docs.plandex.ai/install  
- Plandex Cloud wind-down: https://plandex.ai/blog/winding-down  
- Plandex local mode quickstart: https://docs.plandex.ai/hosting/self-hosting/local-mode-quickstart  
