# Demo Script — Kaggle Video (3–5 minutes)

## Setup (before recording)

1. Start stack: `docker compose up` or local API + Streamlit
2. Pre-load synthetic Jobcenter letter from `tests/fixtures/sample_letters/`
3. Set locale to English in UI

## Script

### 1. Problem (30s)

> "Immigrants in Germany receive complex official letters. Missing a deadline from the Jobcenter or Ausländerbehörde can have serious consequences. Our concierge agent explains these letters in plain language."

### 2. Upload (45s)

- Navigate to **Analyze Letter**
- Upload `jobcenter_nachforderung.txt`
- Show **PII redaction preview**
- Click **Start Analysis**

### 3. Multi-agent pipeline (60s)

- Show progress: Intake → Classifier → Jobcenter Specialist
- Highlight: "Detected: Jobcenter — Nachforderung"
- Show extracted deadline and required documents

### 4. Explanation (45s)

- Read plain-language summary (EN)
- Toggle to DE
- Show glossary tooltips (Bescheid, Mitwirkungspflicht)

### 5. Action plan (45s)

- Show color-coded deadlines
- Export checklist
- Click form link (curated catalog)

### 6. Follow-up concierge (30s)

- Ask: "What happens if I miss this deadline?"
- Show session-aware response

### 7. Security & architecture (30s)

- Mention: PII redaction, not legal advice, GDPR delete
- Show architecture diagram from README

### 8. Close (15s)

> "Built with Google ADK, Gemini 2.5, and MCP. GitHub link in description."

## Fallback

If live demo fails, use pre-recorded analysis JSON from `tests/fixtures/expected_outputs/`.
