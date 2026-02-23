---
doc_id: DOC-SCRIPT-AIDER-SETUP-README-249
---

# Aider + Ollama + DeepSeek-R1 Setup

**Status**: ✅ **CONFIGURED AND READY**

This directory contains scripts to properly configure and run Aider with Ollama and DeepSeek-R1 on Windows.

---

## Quick Start

### Option 1: Permanent Setup (Recommended)

Add environment variables to your PowerShell profile:

```powershell
.\scripts\add-aider-to-profile.ps1
. $PROFILE
```

Then just run:
```powershell
aider
```

### Option 2: Per-Session Setup

Run before each session:
```powershell
.\scripts\set-aider-env.ps1
aider
```

### Option 3: Use Wrapper Script

Always use the wrapper (includes all settings):
```powershell
.\scripts\aider-ollama.ps1
```

---

## Configuration Summary

### Environment Variables Set

| Variable | Value | Purpose |
|----------|-------|---------|
| `PYTHONIOENCODING` | `utf-8` | Fix Windows Unicode encoding crash |
| `PYTHONUTF8` | `1` | Enable Python UTF-8 mode |
| `OLLAMA_API_BASE` | `http://127.0.0.1:11434` | Ollama server endpoint |
| `AIDER_MODEL` | `ollama_chat/deepseek-r1:latest` | Default model |

### Config File Location

Primary config: `C:\Users\richg\.aider.conf.yml`

**Configured with:**
- Main model: `ollama_chat/deepseek-r1:latest`
- Editor model: `ollama_chat/deepseek-r1:latest`
- Weak model: `ollama_chat/deepseek-r1:latest`
- Timeout: 600 seconds
- Stream: false (for stability)
- Auto-commits: true
- Verbose: true

---

## Available Scripts

### `set-aider-env.ps1`
Sets environment variables for the current session.

**Usage:**
```powershell
.\scripts\set-aider-env.ps1
```

### `aider-ollama.ps1`
Wrapper script that sets environment and runs aider.

**Usage:**
```powershell
.\scripts\aider-ollama.ps1 [aider arguments]

# Examples:
.\scripts\aider-ollama.ps1 --help
.\scripts\aider-ollama.ps1 --message "Add error handling to main.py"
.\scripts\aider-ollama.ps1 src/app.py src/utils.py
```

### `test-aider-deepseek.ps1`
Integration test to verify Aider + DeepSeek-R1 is working.

**Usage:**
```powershell
.\scripts\test-aider-deepseek.ps1
```

**What it tests:**
1. Ollama connectivity
2. DeepSeek-R1 model availability
3. Aider can modify code successfully

### `add-aider-to-profile.ps1`
Permanently adds configuration to PowerShell profile.

**Usage:**
```powershell
.\scripts\add-aider-to-profile.ps1
. $PROFILE  # Reload profile
```

---

## Troubleshooting

### Issue 1: "UnicodeEncodeError"

**Cause**: Terminal encoding not set to UTF-8

**Fix**: Use one of the setup scripts above, or manually set:
```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
```

### Issue 2: "OllamaError: Connection refused"

**Cause**: Ollama server not running

**Fix**:
```powershell
# Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# Start Ollama (choose one):
# Option A: Launch from Start Menu > "Ollama"
# Option B: Run in terminal
ollama serve
```

### Issue 3: "Model not found"

**Cause**: DeepSeek-R1 not pulled

**Fix**:
```powershell
ollama pull deepseek-r1:latest
ollama list  # Verify it's installed
```

### Issue 4: Environment variable conflict

**Symptoms**: Aider uses wrong model

**Check**:
```powershell
echo $env:AIDER_MODEL
# Should be: ollama_chat/deepseek-r1:latest
```

**Fix**: Run `set-aider-env.ps1` or reload profile

---

## Model Information

### DeepSeek-R1 (8.2B)
- **Size**: 5.2 GB
- **Type**: Chat model with reasoning capabilities
- **Strengths**: Code generation, explanation, debugging
- **Context**: 64K tokens (configured)

### Alternative Models Available

Your Ollama installation also has:
- `deepseek-coder:latest` (776 MB) - Smaller code model
- `qwen2.5-coder:7b` (4.7 GB) - Alternative code model
- `deepcoder:14b` (9.0 GB) - Larger code model

To switch models, edit `~/.aider.conf.yml` and update:
```yaml
model: ollama_chat/[model-name]
```

---

## Integration with AIM Pipeline

The wrapper script can be used with AIM adapters:

**From `aim\.AIM_ai-tools-registry\AIM_adapters\AIM_aider.ps1`:**

```powershell
# The adapter already handles environment setup
# Just ensure Ollama is running before executing workstreams
```

---

## Testing Your Setup

### Quick Test (30 seconds)
```powershell
.\scripts\test-aider-deepseek.ps1
```

### Manual Test (Interactive)
```powershell
# 1. Set environment
.\scripts\set-aider-env.ps1

# 2. Create test file
echo "def hello(): pass" > test.py

# 3. Run aider
aider --message "Add a docstring to the hello function" --yes test.py
```

### Expected Success Output
```
Starting Aider with DeepSeek-R1...
Aider v0.86.1
Model: ollama_chat/deepseek-r1:latest
[File changes shown]
Applied edit to test.py
```

---

## Common Workflows

### Workflow 1: Quick Code Edit
```powershell
.\scripts\aider-ollama.ps1 --message "Fix the bug in login.py" src/login.py
```

### Workflow 2: Interactive Session
```powershell
.\scripts\aider-ollama.ps1
# Then chat interactively with aider
```

### Workflow 3: Pipeline Integration
```powershell
# Run workstream with aider
python scripts/run_workstream.py --ws-id example_single
```

---

## Files Modified/Created

| File | Status | Purpose |
|------|--------|---------|
| `~/.aider.conf.yml` | ✅ Updated | Main configuration |
| `scripts/set-aider-env.ps1` | ✅ Created | Session env setup |
| `scripts/aider-ollama.ps1` | ✅ Updated | Wrapper script |
| `scripts/test-aider-deepseek.ps1` | ✅ Created | Integration test |
| `scripts/add-aider-to-profile.ps1` | ✅ Created | Profile installer |
| `scripts/AIDER_SETUP_README.md` | ✅ Created | This file |

---

## What Was Fixed

1. ✅ **Unicode encoding crash** - Set `PYTHONIOENCODING=utf-8`
2. ✅ **Model configuration** - Aligned to use `deepseek-r1:latest`
3. ✅ **Environment variables** - Created scripts to manage them
4. ✅ **Permanent setup** - Profile integration available
5. ✅ **Testing** - Integration test script created

---

## Next Steps

1. **Choose your setup method** (permanent, per-session, or wrapper)
2. **Run the test** to verify everything works
3. **Start using Aider** for your development tasks

**Need help?** Check the troubleshooting section above or refer to:
- Aider docs: https://aider.chat/docs/
- Your configuration history: `C:\Users\richg\ALL_AI\Migrate Codex & adier WSL2 on Windows\`

---

*Last updated: 2025-11-22*
*Configuration target: DeepSeek-R1 via Ollama on Windows*
