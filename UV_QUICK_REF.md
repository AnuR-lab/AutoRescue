# ⚡ UV Quick Reference - AutoRescue

## 🚀 Start Streamlit (Your App)
```bash
uv run streamlit run app.py
```
**Access:** http://localhost:8501

---

## 📦 Common Commands

| Task | Command |
|------|---------|
| **Run Streamlit** | `uv run streamlit run app.py` |
| **Run Python script** | `uv run python script.py` |
| **Install dependencies** | `uv sync` |
| **Add package** | `uv add package-name` |
| **Add dev package** | `uv add --dev package-name` |
| **Remove package** | `uv remove package-name` |
| **Update all** | `uv sync --upgrade` |
| **List packages** | `uv pip list` |
| **Activate venv** | `source .venv/bin/activate` |

---

## 🎯 AutoRescue Specific

```bash
# Start Streamlit UI
uv run streamlit run app.py

# Test Agent
uv run python scripts/test_agent_local.py

# Deploy Lambda Functions (uses own packaging)
./scripts/deploy_sam.sh
```

---

## ⚡ Speed Comparison

| Tool | Time to Install 55 Packages |
|------|----------------------------|
| pip | 45-60 seconds |
| **UV** | **8-10 seconds** ⚡ |

**UV is 5-7x faster!**

---

## 📁 Important Files

- **`pyproject.toml`** - Project config & dependencies
- **`uv.lock`** - Lock file (commit to git!)
- **`.venv/`** - Virtual environment (don't commit)
- **`.python-version`** - Python version (3.12)

---

## 🔥 Pro Tips

1. **No need to activate venv** - Just use `uv run`
2. **Commit uv.lock** - Ensures reproducible builds
3. **Use UV for all packages** - Don't mix with pip
4. **Check for updates** - Run `uv sync --upgrade` regularly

---

**Documentation:** See `UV_SETUP.md` for full guide

**Current Status:**
- ✅ UV 0.9.3 installed
- ✅ Python 3.12.12
- ✅ 55 packages synced
- ✅ Streamlit running on http://localhost:8501
