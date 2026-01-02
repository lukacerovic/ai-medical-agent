# CrewAI Medical Agent - Quick Installation Guide

## Prerequisites

- Python 3.10+ (required for CrewAI)
- pip (Python package manager)
- Git

## Quick Setup (5 minutes)

### Step 1: Clone & Navigate
```bash
git clone https://github.com/lukacerovic/ai-medical-agent.git
cd ai-medical-agent
git checkout CREWAI_V
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies (NEW METHOD)
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

**IMPORTANT:** The new requirements.txt has NO version pinning. This allows pip to automatically resolve dependency conflicts between pydantic, fastapi, crewai, and openai.

### Step 4: Configure .env
```bash
# In backend/ directory, create .env file with:
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
```

### Step 5: Run Backend
```bash
uvicorn app.main:app --reload --port 8000
```

### Step 6: Run Frontend (new terminal)
```bash
cd frontend
npm install
npm start
```

## If pip install STILL fails:

### Option A: Install Core Packages Separately
```bash
pip install fastapi uvicorn python-multipart
pip install crewai crewai-tools
pip install openai langchain
pip install pandas numpy
pip install python-dotenv
```

### Option B: Complete Clean Install
```bash
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate
pip install --upgrade pip setuptools wheel
cd backend
pip install -r requirements.txt
```

## Key Points

1. **No version conflicts** - New requirements.txt lets pip decide compatible versions
2. **Pydantic auto-resolved** - No more 2.5.2 vs 2.6.1 conflicts
3. **FastAPI compatible** - Works with pydantic >=1.7.4, <3.0.0
4. **CrewAI ready** - Supports CrewAI 0.28.8 with proper dependencies

## Verification

After installation, test with:
```bash
python -c "import fastapi; import crewai; import openai; print('All OK!')"
```

## Troubleshooting Quick Reference

| Error | Solution |
|-------|----------|
| No module 'openai' | `pip install openai` |
| Pydantic conflicts | Reinstall with clean venv |
| Port 8000 in use | `uvicorn app.main:app --port 8001` |
| Module 'app' not found | Run from backend/ directory |

Done! App runs at http://localhost:3000
