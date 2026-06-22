"""Normalize priority files to UTF-8 without BOM and LF line endings."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

README = r"""# German Bureaucracy AI Agent

**Kaggle Capstone - Concierge Agents - Google ADK + Gemini 2.5 + MCP**

A multi-agent concierge that helps immigrants in Germany understand official letters from Jobcenter, Finanzamt, Auslaenderbehoerde, and Krankenkasse.

> **Not legal advice.** AI-generated summaries only. See [DISCLAIMER.md](DISCLAIMER.md).

---

## For judges (60-second overview)

| Requirement | How this project demonstrates it |
|-------------|----------------------------------|
| Google ADK multi-agent | `SequentialAgent` orchestrator with 3 `LlmAgent` specialists |
| Gemini | Flash (classifier) + Pro (extraction, response writer) |
| MCP | `glossary_lookup` + `deadline_calculator` in `mcp_servers/bureaucracy_mcp/` |
| Security | PII redaction before LLM; audit log stores hash only; legal disclaimer |
| Deployable | `pip install` + `streamlit run` on Windows, macOS, Linux |

**Demo flow:** Load sample Jobcenter letter -> Analyze -> institution, deadlines, checklist, German reply draft.

---

## Architecture

```mermaid
flowchart TB
    UI[Streamlit UI] --> PIPE[analyze_letter]
    PIPE --> SEC[PII Redaction]
    SEC --> ORCH[ADK SequentialAgent]
    ORCH --> C[classifier_agent<br/>Gemini 2.5 Flash]
    ORCH --> E[extraction_agent<br/>Gemini 2.5 Pro]
    ORCH --> R[response_writer_agent<br/>Gemini 2.5 Pro]
    C & E & R --> MCP[MCP Tools]
    MCP --> GL[glossary_lookup]
    MCP --> DC[deadline_calculator]
    PIPE --> LOG[Audit log hash only]
    R --> OUT[Summary + Checklist + Reply]
```

---

## Quick start (Windows)

```powershell
cd kaggle-project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env: set GOOGLE_API_KEY=your-key
python -m streamlit run apps\streamlit_app\app.py
```

Open http://localhost:8501 -> sidebar **Load sample Jobcenter letter** -> **Analyze letter**.

**Shortcut:** `.\scripts\run_mvp.ps1`

---

## Quick start (macOS / Linux)

```bash
cd kaggle-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set GOOGLE_API_KEY=your-key
streamlit run apps/streamlit_app/app.py
```

---

## Screenshots

Add before submission:

| # | File | What to show |
|---|------|--------------|
| 1 | `docs/screenshots/01_home.png` | Home screen with sample letter loaded |
| 2 | `docs/screenshots/02_results.png` | Institution, summary, deadlines |
| 3 | `docs/screenshots/03_checklist.png` | Action checklist and German reply |
| 4 | `docs/screenshots/04_technical.png` | Technical details expander (ADK + MCP) |

---

## Tests

```powershell
python -m pytest tests\unit\ -v
```

---

## MCP server (optional)

```powershell
python -m mcp_servers.bureaucracy_mcp.server
```

---

## Kaggle submission

| Document | Purpose |
|----------|---------|
| [docs/kaggle_writeup.md](docs/kaggle_writeup.md) | Paste into Kaggle writeup |
| [docs/video_demo_script.md](docs/video_demo_script.md) | 5-minute video script |
| [docs/judging_checklist.md](docs/judging_checklist.md) | Pre-submit verification |

---

## Project structure (MVP)

```
agents/                      ADK orchestrator + 3 agents + pipeline
apps/streamlit_app/          Demo UI
mcp_servers/bureaucracy_mcp/ MCP tools
knowledge/glossary/          Curated terms
tests/fixtures/              Sample Jobcenter letter
```

---

## Security

- Only `GOOGLE_API_KEY` required (via `.env`, never committed)
- PII redacted before Gemini calls (`agents/security.py`)
- Audit log: institution + letter type + SHA-256 hash only

---

## License

Apache 2.0 - see [LICENSE](LICENSE)
"""

REQUIREMENTS = """google-adk>=1.35.0
google-genai>=1.0.0
mcp>=1.6.0
streamlit>=1.41.0
pypdf>=5.1.0
python-dotenv>=1.0.1
pydantic-settings>=2.6.0
pyyaml>=6.0.2
"""

ENV_EXAMPLE = """# German Bureaucracy AI Agent - Environment (MVP)

# Required: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your-google-api-key-here

# Optional model overrides
GEMINI_MODEL_FLASH=gemini-2.5-flash
GEMINI_MODEL_PRO=gemini-2.5-pro

# Security
PII_REDACTION_ENABLED=true
"""

PRIORITY_FILES: list[str] = [
    "apps/streamlit_app/app.py",
    "agents/pipeline.py",
    "agents/root_orchestrator.py",
    "agents/classifier_agent.py",
    "agents/extraction_agent.py",
    "agents/response_writer_agent.py",
    "agents/tools/mcp_tools.py",
    "mcp_servers/bureaucracy_mcp/tools.py",
]


def write_lf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def normalize_existing(path: Path) -> None:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    write_lf(path, text)


def main() -> None:
    write_lf(ROOT / "README.md", README)
    write_lf(ROOT / "requirements.txt", REQUIREMENTS)
    write_lf(ROOT / ".env.example", ENV_EXAMPLE)

    for rel in PRIORITY_FILES:
        p = ROOT / rel
        if p.exists():
            normalize_existing(p)
            print(f"normalized: {rel}")

    print("done")


if __name__ == "__main__":
    main()
