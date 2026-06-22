# Kaggle Submission Checklist

Use this before clicking **Submit** on Kaggle.

---

## Required concepts (verify in demo)

- [ ] **Google ADK multi-agent** — `agents/root_orchestrator.py` → `SequentialAgent` + 3 agents
- [ ] **Gemini 2.5** — Flash (classifier) + Pro (extraction, writer) in agent files
- [ ] **MCP server** — `glossary_lookup` + `deadline_calculator` in `mcp_servers/bureaucracy_mcp/`
- [ ] **Security** — PII redaction banner + disclaimer + no secrets in repo
- [ ] **Deployable** — `requirements.txt` + Streamlit one-command run

---

## Pre-submit smoke test (Windows)

```powershell
cd kaggle-project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Set GOOGLE_API_KEY in .env
python -m pytest tests\unit\ -v
python -m streamlit run apps\streamlit_app\app.py
```

- [ ] 12 unit tests pass
- [ ] App loads at http://localhost:8501
- [ ] Sample letter loads
- [ ] Analysis completes (< 60 s)
- [ ] All result sections render

---

## Secrets audit

```powershell
git status
# Confirm .env is NOT listed (only .env.example)
```

- [ ] No `.env` committed
- [ ] No `AIza…` keys in any tracked file
- [ ] `.gitignore` covers `.env`, `data/logs/`, `.streamlit/secrets.toml`

---

## Kaggle form

- [ ] **Title:** German Bureaucracy AI Agent — Concierge for Official Letters
- [ ] **Writeup:** paste from `docs/kaggle_writeup.md` (< 2,500 words)
- [ ] **GitHub URL:** public repo link
- [ ] **Video:** 5-min demo per `docs/video_demo_script.md`
- [ ] **Screenshots:** add to `docs/screenshots/` and embed in README (optional but recommended)

---

## Demo day checklist

- [ ] API key valid and quota available
- [ ] Sample letter tested same day
- [ ] Fallback recording ready if API fails
- [ ] README links work
- [ ] DISCLAIMER visible in app

---

## Honest limitations (say once in video/writeup)

- Not legal advice
- Bundesland rules vary
- Scanned PDFs may not work without OCR
