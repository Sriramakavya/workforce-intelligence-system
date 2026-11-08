# GitHub publishing steps (Windows PowerShell)

1. Extract the submission ZIP into a new folder. Do not overwrite an earlier working copy until you have backed it up.
2. Open the extracted `workforce-intelligence-system` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create/activate the environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

5. Run and verify before publishing:

```powershell
python main.py --scale starter --seed 20261022
pytest -q
python -m src.reproducibility --scale starter --seed 20261022
```

6. On GitHub, choose New repository. Name it `workforce-intelligence-demand-forecasting`. Set visibility to Public. Do not initialize it with a README, .gitignore, or license because this folder already contains those files.
7. Copy the new repository HTTPS URL from GitHub. In the VS Code terminal, run the following commands, replacing the placeholder URL with your own repository URL:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Build workforce intelligence and demand forecasting system"
git remote add origin https://github.com/YOUR-USERNAME/workforce-intelligence-demand-forecasting.git
git push -u origin main
```

8. If Git asks you to configure your identity, use your own GitHub commit name/email:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Then repeat the commit command and push.

9. Open the repository URL in a private/incognito browser window. Confirm it is Public and that README, source, tests, docs, starter CSV/JSON/SQLite outputs, prompt history, and `artifacts/full_scale_bundle.zip` are visible.
10. Complete `docs/verification_checklist.md`, especially the prompt-history review. Add every exact prompt used in other chats or AI coding tools to `PROMPT_HISTORY.md`; do not claim the current log is exhaustive if it is not.
11. Return to the YottaFlex application, paste the public repository URL into the GitHub repository URL field, and submit before the deadline. The brief says submission is final once sent, so verify the URL and public access before clicking Submit.
