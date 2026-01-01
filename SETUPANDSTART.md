Windows - Using Chocolatey:

powershell
# Open PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force
choco install ffmpeg

Verify:

powershell
ffmpeg -version


2.2 Install Python 3.10+
Download from https://www.python.org/downloads/

✅ Check "Add Python to PATH" during installation

Verify:

powershell
python --version
2.3 Install Node.js 16+
Download from https://nodejs.org/

Use LTS version

Verify:

powershell
node --version
npm --version
2.4 Install Git
Download from https://git-scm.com/

Use default installation

Verify:

powershell
git --version
🐍 STEP 3: BACKEND SETUP
3.1 Navigate to Backend
powershell
cd backend
3.2 Create Virtual Environment
powershell
python -m venv venv
.\venv\Scripts\activate
You should see (venv) in your prompt.

3.3 Install Python Dependencies
powershell
pip install -r requirements.txt
