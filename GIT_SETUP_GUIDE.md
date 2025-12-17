# Git Setup and GitHub Push Guide

## Step 1: Install Git

1. **Download Git for Windows**:
   - Open your browser and go to: https://git-scm.com/download/win
   - The download should start automatically
   - Run the installer (Git-2.XX.X-64-bit.exe)

2. **Installation Options**:
   - Use default settings for all options
   - Important: Make sure "Git from the command line and also from 3rd-party software" is selected
   - Click "Next" through all screens and "Install"

3. **Verify Installation**:
   - **Close and reopen your PowerShell/Terminal** (important!)
   - Run: `git --version`
   - You should see something like: `git version 2.43.0.windows.1`

---

## Step 2: Configure Git (One-Time Setup)

Open PowerShell and run these commands (replace with your actual info):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Note**: Use the email associated with your GitHub account!

---

## Step 3: Initialize Local Repository

Navigate to your project folder and initialize Git:

```powershell
cd C:\Users\ravi_\.gemini\antigravity\scratch\risk_adjusted_calls
git init
git add .
git commit -m "Initial commit: Risk-Adjusted Covered Call Analyzer with Streamlit UI"
```

**What this does**:
- `git init` - Creates a new Git repository
- `git add .` - Stages all files for commit
- `git commit` - Saves the snapshot with a message

---

## Step 4: Create GitHub Repository

1. **Go to GitHub**:
   - Visit: https://github.com/new
   - OR: Go to https://github.com and click the "+" icon → "New repository"

2. **Repository Settings**:
   - **Repository name**: `risk-adjusted-covered-calls` (or your preferred name)
   - **Description**: "Streamlit app for analyzing covered call options using Schwab API with stability scoring"
   - **Public** or **Private**: Your choice
   - ❌ **DO NOT** check "Add a README file" (you already have one)
   - ❌ **DO NOT** add .gitignore (you already have one)
   - Click **"Create repository"**

3. **Copy the Repository URL**:
   - After creation, you'll see a page with setup instructions
   - Look for the HTTPS URL: `https://github.com/YOUR_USERNAME/risk-adjusted-covered-calls.git`
   - Copy this URL

---

## Step 5: Connect Local Repository to GitHub

Run these commands (replace YOUR_USERNAME with your actual GitHub username):

```powershell
git remote add origin https://github.com/YOUR_USERNAME/risk-adjusted-covered-calls.git
git branch -M main
git push -u origin main
```

**If prompted for credentials**:
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your password)
  - Create token at: https://github.com/settings/tokens
  - Click "Generate new token (classic)"
  - Give it a name like "Git CLI Access"
  - Check at minimum: `repo` scope
  - Generate and copy the token
  - Use this token as your password

---

## Step 6: Verify Upload

1. Go to your repository on GitHub: `https://github.com/YOUR_USERNAME/risk-adjusted-covered-calls`
2. You should see all your files:
   - app.py
   - schwab_wrapper.py
   - technicals.py
   - requirements.txt
   - README.md
   - CHANGES.md
   - .gitignore

---

## Future Updates

When you make changes to your code:

```powershell
cd C:\Users\ravi_\.gemini\antigravity\scratch\risk_adjusted_calls
git add .
git commit -m "Description of what you changed"
git push
```

---

## Troubleshooting

### Problem: "fatal: not a git repository"
**Solution**: You're not in the right folder. Run `cd C:\Users\ravi_\.gemini\antigravity\scratch\risk_adjusted_calls`

### Problem: "git: command not found"
**Solution**: Git isn't installed or terminal wasn't restarted. Close terminal, reopen, try again.

### Problem: Authentication failed
**Solution**: Use a Personal Access Token instead of password (see Step 5)

### Problem: "refusing to merge unrelated histories"
**Solution**: You may have initialized the GitHub repo with files. Try:
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## Next Steps After Push

Consider adding:
- **GitHub Actions**: Automated testing
- **Branch protection**: Prevent direct commits to main
- **Issues/Projects**: Track features and bugs
- **Wiki**: Extended documentation
