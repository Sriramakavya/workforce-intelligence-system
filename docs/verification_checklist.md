# Candidate verification checklist

Complete this checklist yourself before publishing. Do not mark a step complete unless you personally ran or inspected it.

- [ ] Read the README, assumptions, data dictionary, schema and source code.
- [ ] Run starter workflow: `python main.py --scale starter`.
- [ ] Confirm all rows in `outputs/validation_report.csv` pass.
- [ ] Run tests: `pytest -q`.
- [ ] Inspect the four issue types in `data/ground_truth/ground_truth.csv` and `outputs/detected_anomalies.csv`.
- [ ] Confirm `outputs/forecast_metrics.json` contains holdout MAE, RMSE and naive MAE.
- [ ] Open the dashboard with `streamlit run app/dashboard.py`.
- [ ] Run the full-scale workflow: `python main.py --scale full` (check available RAM and disk first).
- [ ] Regenerate starter data with the same seed and compare checksums.
- [ ] Add every actual AI prompt used to `PROMPT_HISTORY.md`.
- [ ] Remove any local secrets or personal files; verify `.gitignore`.
- [ ] Create a dedicated public GitHub repository and push the project.
- [ ] Open the public repository in a private/incognito browser window to confirm visibility.
- [ ] Submit the repository URL from the same email address used in recruitment.
