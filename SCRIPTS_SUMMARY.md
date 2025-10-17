# AgentCore Update Scripts - Summary

## ✅ Created Scripts

### 1. **`scripts/update_agent.sh`** (Shell Script)
- **Purpose**: Update AgentCore runtime using the `agentcore launch` command
- **Functionality**: Automatically builds Docker image, pushes to ECR, and deploys runtime
- **Platform**: macOS/Linux (bash)

### 2. **`scripts/update_agent.py`** (Python Script)
- **Purpose**: Cross-platform alternative to the shell script
- **Functionality**: Same as shell script but works on Windows, macOS, and Linux
- **Features**:
  - Reads `.bedrock_agentcore.yaml` to show agent configuration
  - Displays agent name and ARN before deployment
  - Provides helpful test commands after successful deployment
  - Comprehensive error handling

### 3. **`scripts/README.md`** (Documentation)
- **Purpose**: Comprehensive guide for all deployment scripts
- **Contents**:
  - Description of all available scripts
  - Usage examples
  - Common workflows
  - Prerequisites and setup
  - Troubleshooting guide

## 🔧 How It Works

The `agentcore launch` command performs three operations in sequence:

1. **Build**: Creates a Docker image from your `Dockerfile` and agent code
2. **Push**: Uploads the image to AWS ECR (Elastic Container Registry)
3. **Deploy**: Updates the AgentCore runtime to use the new image

## 📖 Usage

### Quick Update (Shell)
```bash
./scripts/update_agent.sh
```

### Quick Update (Python)
```bash
python scripts/update_agent.py
```

### After Update
```bash
# Test the agent
cd agent_runtime
uv run agentcore invoke '{"prompt": "Find flights from JFK to LAX on October 23, 2025"}'

# Check status
uv run agentcore status

# View logs
uv run agentcore logs --follow
```

## 🔄 When to Use

Use these scripts when you:
- Update agent code (`autorescue_agent.py`)
- Change the system prompt
- Modify environment variables
- Update Python dependencies
- Change the model (e.g., upgrading to Claude Sonnet 4.5)

## 📁 Files Modified

- `scripts/update_agent.sh` (NEW) - Shell script
- `scripts/update_agent.py` (NEW) - Python script  
- `scripts/README.md` (NEW) - Documentation
- `README.md` (UPDATED) - Added script references to Quick Start

## ✨ Key Features

1. **Automatic Detection**: Reads agent configuration from `.bedrock_agentcore.yaml`
2. **Clear Progress**: Shows step-by-step progress with emojis
3. **Error Handling**: Exits gracefully on failures with helpful messages
4. **Post-Deployment Help**: Provides test commands after successful deployment
5. **Cross-Platform**: Python version works on all platforms

## 🎯 Benefits

- **One Command**: No need to manually run build, push, and deploy separately
- **Idempotent**: Safe to run multiple times
- **Self-Documenting**: Clear output explains what's happening
- **Tested**: Works with current AutoRescue agent configuration

## 📚 Documentation

All scripts are fully documented in:
- Individual file comments
- `scripts/README.md` for comprehensive guide
- Main `README.md` for quick reference

---

**Created**: October 16, 2025  
**Status**: ✅ Deployed and tested  
**Commits**: 
- `6cb3f6c`: feat: Add AgentCore runtime update scripts
- `1c84aaf`: docs: Update Quick Start with script references
