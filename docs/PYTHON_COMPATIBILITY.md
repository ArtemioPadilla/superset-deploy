# Python Version Compatibility Guide

## Supported Python Versions

This project supports **Python 3.8 through 3.11**, with **Python 3.11 being the recommended version** for best compatibility and performance.

## Why Python 3.11?

### 1. **Optimal Compatibility**
- All dependencies (Pulumi, Pydantic v2, etc.) are fully tested with Python 3.11
- Python 3.13 is too new and may have compatibility issues with some packages
- Python 3.11 is mature and stable (released October 2022)

### 2. **Performance Benefits**
- Python 3.11 is up to 25% faster than Python 3.10
- Significantly improved error messages and debugging
- Better memory usage and startup time

### 3. **Long-term Support**
- Python 3.11 will receive security updates until October 2027
- Wide ecosystem support across all major cloud providers
- Docker official images are well-maintained for Python 3.11

## Version Compatibility Matrix

| Python Version | Support Status | Notes |
|----------------|----------------|-------|
| 3.8            | ✅ Supported   | Minimum version, missing some performance improvements |
| 3.9            | ✅ Supported   | Stable, but consider upgrading |
| 3.10           | ✅ Supported   | Good compatibility |
| **3.11**       | ✅ **Recommended** | **Best performance and compatibility** |
| 3.12           | ⚠️  Use with caution | May work but not tested |
| 3.13           | ❌ Not supported | Too new, compatibility issues expected |

## Setting Up Python 3.11

### macOS (using Homebrew)
```bash
brew install python@3.11
python3.11 -m venv .venv
source .venv/bin/activate
```

### macOS/Linux (using pyenv)
```bash
pyenv install 3.11.9
pyenv local 3.11.9
python -m venv .venv
source .venv/bin/activate
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
python3.11 -m venv .venv
source .venv/bin/activate
```

### Windows
Download Python 3.11 from [python.org](https://www.python.org/downloads/) or use:
```powershell
winget install Python.Python.3.11
python -m venv .venv
.venv\Scripts\activate
```

## Docker Considerations

The project's Docker images use Python 3.11 by default. If you need to use a different version:

1. Update `.env` file:
   ```bash
   PYTHON_VERSION=3.11
   ```

2. Build custom Superset image if needed:
   ```dockerfile
   FROM python:3.11-slim
   # ... rest of Dockerfile
   ```

## Dependency Compatibility

All project dependencies are tested with Python 3.11:

- **Pulumi**: ✅ Full support
- **Pydantic v2**: ✅ Optimized for Python 3.11
- **Apache Superset**: ✅ Officially supports Python 3.11
- **Google Cloud SDK**: ✅ Full support
- **Cloudflare SDK**: ✅ Full support

## Troubleshooting

### Issue: Python version not found
```bash
# Check available Python versions
which python3.11
python3 --version

# Install Python 3.11 if needed (see setup instructions above)
```

### Issue: Virtual environment using wrong Python
```bash
# Remove existing virtual environment
rm -rf .venv

# Create new one with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate
python --version  # Should show Python 3.11.x
```

### Issue: Package compatibility errors
```bash
# Clear pip cache
pip cache purge

# Reinstall with Python 3.11
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## CI/CD Configuration

The project's CI/CD pipeline tests against multiple Python versions but uses Python 3.11 as the primary version:

- GitHub Actions: Tests Python 3.8-3.11
- Docker builds: Uses Python 3.11
- Production deployments: Recommended to use Python 3.11

## Future Python Support

- **Python 3.12**: Will be evaluated once all dependencies confirm support
- **Python 3.13**: Will be supported after ecosystem stabilizes (likely mid-2025)
- **Python 3.8**: Support will be dropped when it reaches end-of-life (October 2024)