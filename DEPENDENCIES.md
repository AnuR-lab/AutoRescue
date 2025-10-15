# Dependency Management - AutoRescue

## 📦 Requirements Files

We now have **pinned dependencies** for reproducible builds:

### 1. `requirements.txt` (Production)
Main dependencies with exact versions for production deployment.

**Install:**
```bash
pip install -r requirements.txt
```

### 2. `requirements-dev.txt` (Development)
Additional tools for development, testing, and code quality.

**Install:**
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. `pyproject.toml` (Project Metadata)
Modern Python project configuration with pinned dependencies.

**Install:**
```bash
pip install -e .
```

---

## 🔒 Pinned Versions (October 15, 2025)

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `agentcore` | `>=0.1.0` | AWS Bedrock AgentCore framework (flexible - in development) |
| `boto3` | `==1.40.52` | AWS SDK for Python |
| `botocore` | `==1.40.52` | Low-level AWS client library |
| `requests` | `==2.32.5` | HTTP library for API calls |
| `python-dotenv` | `==1.1.1` | Environment variable management |
| `streamlit` | `==1.50.0` | Web UI framework |
| `streamlit-authenticator` | `==0.4.2` | Authentication for Streamlit |
| `watchdog` | `==6.0.0` | File system monitoring |
| `pydantic` | `==2.10.5` | Data validation |
| `typing-extensions` | `==4.12.2` | Type hints backport |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | `==8.3.4` | Testing framework |
| `black` | `==24.10.0` | Code formatter |
| `flake8` | `==7.1.2` | Linter |
| `mypy` | `==1.14.1` | Type checker |
| `pylint` | `==3.3.3` | Code analysis |
| `isort` | `==5.13.2` | Import sorter |

---

## 🚀 Installation Guide

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt

# Or install with development tools
pip install -r requirements.txt -r requirements-dev.txt
```

### Option 2: Using pyproject.toml

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install project in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Option 3: Using UV (Fast Package Manager)

```bash
# Install using uv (faster than pip)
uv pip install -r requirements.txt

# With dev dependencies
uv pip install -r requirements.txt -r requirements-dev.txt
```

---

## 🔄 Updating Dependencies

### Check for Updates

```bash
# Check outdated packages
pip list --outdated

# Or use pip-tools
pip install pip-tools
pip-compile --upgrade requirements.in
```

### Update Specific Package

```bash
# Example: Update boto3
pip install --upgrade boto3==<new-version>

# Then update requirements.txt with the new version
```

### Regenerate Lock File

```bash
# Using pip-tools
pip-compile requirements.in --output-file requirements.txt

# Or manually check latest versions
python3 -m pip index versions <package-name>
```

---

## 📝 Why Pin Dependencies?

✅ **Reproducibility**: Same versions across all environments  
✅ **Stability**: Avoid breaking changes from automatic updates  
✅ **Security**: Know exactly which versions are deployed  
✅ **Debugging**: Easier to track issues to specific versions  
✅ **CI/CD**: Consistent builds in pipelines  

---

## ⚠️ Important Notes

### AgentCore Version

`agentcore>=0.1.0` is kept flexible because:
- Still in active development by AWS
- Frequent updates and improvements
- Backward compatibility maintained
- Will pin to specific version when it reaches 1.0.0

### AWS SDK Compatibility

- `boto3` and `botocore` versions must be compatible
- Update both together
- Check AWS SDK changelog for breaking changes

### Streamlit UI

- Streamlit 1.50.0 is latest stable
- Includes all dependencies for web UI
- Compatible with Python 3.12+

---

## 🔍 Dependency Tree

```
AutoRescue
├── agentcore (>=0.1.0)
│   └── AWS Bedrock integration
├── boto3 (1.40.52)
│   ├── botocore (1.35.52)
│   ├── jmespath
│   └── s3transfer
├── requests (2.32.5)
│   ├── urllib3 (2.3.0)
│   ├── certifi (2024.10.1)
│   ├── charset-normalizer (3.4.1)
│   └── idna (3.10)
├── streamlit (1.50.0)
│   ├── altair (5.5.0)
│   ├── numpy (2.2.4)
│   ├── pandas (2.2.3)
│   ├── pillow (11.1.0)
│   └── ... (many more)
└── pydantic (2.10.5)
    ├── pydantic-core (2.27.2)
    ├── typing-extensions (4.12.2)
    └── annotated-types (0.7.0)
```

---

## 🧪 Testing Dependencies

After installation, verify:

```bash
# Check installed versions
pip list

# Verify core packages
python3 -c "import boto3; print(f'boto3: {boto3.__version__}')"
python3 -c "import requests; print(f'requests: {requests.__version__}')"
python3 -c "import streamlit; print(f'streamlit: {streamlit.__version__}')"

# Run tests (if available)
pytest tests/
```

---

## 📅 Last Updated

**Date**: October 15, 2025  
**Python Version**: 3.12+  
**Platform**: macOS, Linux, Windows  
**Next Review**: December 15, 2025  

---

## 🔗 References

- [Python Packaging Guide](https://packaging.python.org/)
- [pip-tools Documentation](https://pip-tools.readthedocs.io/)
- [AWS SDK for Python (Boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
