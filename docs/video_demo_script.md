# Video Demo Script (5:00)

**Project:** German Bureaucracy AI Agent  
**Target length:** 4:45–5:00 (leave 15s buffer)

---

## Pre-recording (off camera)

- [ ] `GOOGLE_API_KEY` in `.env`
- [ ] Run: `python -m streamlit run apps\streamlit_app\app.py`
- [ ] Browser at http://localhost:8501, zoom 110%
- [ ] Close notifications; hide bookmarks bar

---

## 0:00–0:25 | Hook

**[Screen: empty app]**

> "In Germany, one official letter can change your benefits, taxes, or residence status — and they're written in bureaucratic German. This concierge agent reads the letter for you and tells you exactly what to do."

---

## 0:25–0:50 | Architecture

**[Screen: sidebar]**

> "Three Google ADK agents run in sequence — classify, extract, respond — powered by Gemini 2.5. Two MCP tools handle glossary lookups and deadline math. Personal data is redacted before anything reaches the model or logs."

---

## 0:50–1:30 | Load sample + security

**[Action: Load sample Jobcenter letter]**

> "Here's a real Jobcenter Nachforderung — a request for missing documents, deadline July 15th."

**[Point to letter text]**

> "Names and case numbers get redacted. Logs store only a hash. Every result carries a legal disclaimer — this is information, not legal advice."

---

## 1:30–3:15 | Live analysis

**[Action: Analyze letter — wait for spinner]**

> "Classifier detects Jobcenter. Extractor pulls the deadline and three required documents. Response writer explains in English and drafts a German reply."

**[Walk through results — ~90 seconds]**

1. Institution: **Jobcenter**
2. Summary — read one sentence aloud
3. Deadlines — **15.07.2025**
4. Required documents — Meldebescheinigung, Kontoauszüge, Mietvertrag
5. Action checklist — urgency icons
6. German reply draft — scroll briefly

---

## 3:15–3:50 | Technical proof

**[Action: expand Technical details (for judges)]**

> "This is a real ADK SequentialAgent — three separate LlmAgents, not one mega-prompt. MCP tools: glossary_lookup for Nachforderung, deadline_calculator for the Frist."

---

## 3:50–4:30 | Deployability

**[Optional: flash README or terminal]**

> "Windows setup: venv, pip install, set API key, streamlit run. Twelve unit tests pass without an API key. One command demo script included."

---

## 4:30–4:55 | Close

> "German Bureaucracy AI Agent — Google ADK, Gemini 2.5, MCP, built for the Kaggle Concierge Agents capstone. GitHub and live demo in the description. Thank you."

---

## If API fails during recording

Show a prior successful screen recording, or open `tests/fixtures/sample_letters/jobcenter_nachforderung.txt` and describe expected output.

---

## Timing cheat sheet

| Segment | Duration |
|---------|----------|
| Hook | 0:25 |
| Architecture | 0:25 |
| Sample + security | 0:40 |
| Live analysis | 1:45 |
| Technical proof | 0:35 |
| Deployability | 0:40 |
| Close | 0:25 |
| **Total** | **~4:55** |
