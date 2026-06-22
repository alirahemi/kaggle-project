# Agent Specifications

> German Bureaucracy AI Agent — Google ADK Multi-Agent System  
> Models: **Gemini 2.5 Flash** (routing, classification) · **Gemini 2.5 Pro** (extraction, explanation)

## Agent Registry

| ID | Name | Model | Type | MCP Tools |
|----|------|-------|------|-----------|
| `orchestrator` | Bureaucracy Orchestrator | gemini-2.5-flash | Root `LlmAgent` | — |
| `intake` | Intake Agent | gemini-2.5-flash | Sub-agent | document_mcp.* |
| `classifier` | Classifier Agent | gemini-2.5-flash | Sub-agent | rag_mcp.* |
| `extraction` | Extraction Agent | gemini-2.5-pro | Sub-agent | calendar_mcp.parse_german_date |
| `jobcenter` | Jobcenter Specialist | gemini-2.5-pro | Sub-agent | rag_mcp, gov_resources_mcp |
| `auslaenderbehoerde` | Ausländerbehörde Specialist | gemini-2.5-pro | Sub-agent | rag_mcp, gov_resources_mcp |
| `finanzamt` | Finanzamt Specialist | gemini-2.5-pro | Sub-agent | rag_mcp, gov_resources_mcp |
| `krankenkasse` | Krankenkasse Specialist | gemini-2.5-pro | Sub-agent | rag_mcp, gov_resources_mcp |
| `generic_gov` | Generic Government Specialist | gemini-2.5-pro | Sub-agent | rag_mcp |
| `explainer` | Explainer Agent | gemini-2.5-pro | Sub-agent | rag_mcp.get_glossary_term |
| `action_planner` | Action Planner Agent | gemini-2.5-pro | Sub-agent | calendar_mcp, gov_resources_mcp |
| `safety` | Safety Gate Agent | gemini-2.5-flash | Sub-agent | audit_mcp.log_interaction |

---

## 1. Orchestrator Agent

**File**: `agents/root_orchestrator.py`

### Purpose
Workflow conductor. Routes requests through the letter analysis pipeline. Never answers domain questions directly.

### Input
- User message (text or upload reference)
- Session state: `document_id`, `locale`, `bundesland`

### Output
- Delegation to sub-agents in sequence
- Final packaged `AnalysisResponse`

### Routing Logic
```
IF no document_id → delegate intake
IF no authority → delegate classifier
IF no extraction → delegate extraction
IF authority known → delegate matching specialist
ALWAYS → explainer → action_planner → safety
```

### ADK Configuration
```yaml
name: bureaucracy_orchestrator
model: gemini-2.5-flash
instruction: prompts/orchestrator.yaml
sub_agents: [intake, classifier, extraction, specialists, explainer, action_planner, safety]
callbacks: [pii_guard, schema_validator, disclaimer_injector]
```

### State Keys
- `document_id: str`
- `authority: AuthorityEnum`
- `letter_type: LetterTypeEnum`
- `extraction: LetterExtraction`
- `confidence: float`
- `locale: str` (de|en)
- `bundesland: str` (ISO 3166-2:DE code)

---

## 2. Intake Agent

**File**: `agents/intake_agent.py`

### Purpose
Normalize uploaded documents into machine-readable, PII-redacted text.

### Tasks
1. Parse PDF/text via MCP
2. OCR if scanned (image or low text density)
3. Detect language (de/en)
4. Redact PII before downstream agents
5. Store encrypted document, return `document_id`

### Output Schema
```json
{
  "document_id": "uuid",
  "raw_text": "string (redacted)",
  "language": "de",
  "page_count": 2,
  "document_hash": "sha256",
  "ocr_applied": false
}
```

### Tools
- `document_mcp.parse_document`
- `document_mcp.ocr_document`
- `document_mcp.redact_pii`
- `document_mcp.store_document`

### Error Handling
- Unsupported format → user message with allowed types
- OCR failure → request clearer scan
- Exceeds page limit → truncate with warning

---

## 3. Classifier Agent

**File**: `agents/classifier_agent.py`

### Purpose
Identify issuing authority and letter type.

### Taxonomy

**Authorities** (`AuthorityEnum`):
- `jobcenter`
- `auslaenderbehoerde`
- `finanzamt`
- `krankenkasse`
- `other`

**Letter Types** (`LetterTypeEnum`):
- `bewilligungsbescheid`
- `ablehnungsbescheid`
- `nachforderung`
- `fristsetzung`
- `termin`
- `mahnung`
- `bescheid`
- `other`

### Output Schema
```json
{
  "authority": "jobcenter",
  "letter_type": "nachforderung",
  "confidence": 0.92,
  "reasoning": "References SGB II and Mitwirkungspflicht"
}
```

### Confidence Gate
If `confidence < AGENT_CONFIDENCE_THRESHOLD` (0.75), set `requires_user_confirmation: true`.

### Tools
- `rag_mcp.search_knowledge`
- `rag_mcp.find_similar_cases`

---

## 4. Extraction Agent

**File**: `agents/extraction_agent.py`

### Purpose
Extract structured facts only — no interpretation.

### Model
`gemini-2.5-pro` with JSON schema mode (`config/schemas/letter_extraction.json`)

### Output
See `LetterExtraction` schema in `apps/api_gateway/schemas/analysis.py`

### Rules
- Every deadline must have ISO date or `calendar_mcp.parse_german_date` resolution
- No inferred actions not explicitly stated in letter
- `confidence` reflects extraction completeness

---

## 5. Domain Specialist Agents

**Directory**: `agents/specialists/`

Each specialist validates extraction against domain patterns and enriches context.

### Jobcenter Specialist (`jobcenter_agent.py`)
- **Focus**: ALG II, Bürgergeld, Mitwirkungspflicht, Nachweise
- **Laws**: SGB II, SGB XII
- **Anomaly flags**: Unusual penalty amounts, missing Aktenzeichen format

### Ausländerbehörde Specialist (`auslaenderbehoerde_agent.py`)
- **Focus**: Aufenthaltstitel, Fristen, Duldung, Termine
- **Laws**: AufenthG, AufenthV
- **High-risk**: Deportation-related language → force escalation

### Finanzamt Specialist (`finanzamt_agent.py`)
- **Focus**: Steuerbescheid, Vorauszahlung, Einspruchsfrist
- **Laws**: AO, EStG
- **Tools**: ELSTER form resolution

### Krankenkasse Specialist (`krankenkasse_agent.py`)
- **Focus**: Beiträge, Familienversicherung, Nachweise
- **Laws**: SGB V, SGB XI

### Generic Government Specialist (`generic_gov_agent.py`)
- **Fallback**: Ordnungsamt, Bürgeramt, other Behörden

### Specialist Output Schema
```json
{
  "authority": "jobcenter",
  "validation_passed": true,
  "anomalies": [],
  "domain_context": "string",
  "escalation_required": false
}
```

---

## 6. Explainer Agent

**File**: `agents/explainer_agent.py`

### Purpose
Plain-language explanation for immigrants.

### Constraints
- Must cite extracted fields (deadline dates, amounts)
- No new facts beyond extraction + specialist context
- Bilingual output per `locale` session key
- Mandatory disclaimer block appended

### Output Schema
```json
{
  "summary": "string",
  "key_points": ["string"],
  "glossary_terms": [{"term": "Bescheid", "definition": "..."}],
  "disclaimer": "string",
  "locale": "en"
}
```

### Streaming
Enabled via ADK streaming → API SSE → Streamlit `st.write_stream`

---

## 7. Action Planner Agent

**File**: `agents/action_planner_agent.py`

### Purpose
Prioritized, actionable checklist.

### Output Schema
```json
{
  "urgent": [{"action": "string", "deadline": "ISO", "form_url": "url|null"}],
  "this_week": [],
  "later": [],
  "optional": [],
  "ics_export_available": true
}
```

### Tools
- `calendar_mcp.business_days_until`
- `calendar_mcp.urgency_score`
- `gov_resources_mcp.resolve_form`
- `gov_resources_mcp.get_official_links`

---

## 8. Safety Gate Agent

**File**: `agents/safety_agent.py`

### Purpose
Final output review before user delivery.

### Checks
| Check | Action on failure |
|-------|-------------------|
| Hallucinated deadline not in extraction | Regenerate explainer |
| Missing disclaimer | Inject via callback |
| PII in output text | Block and redact |
| Overconfident legal claim | Downgrade + add caveat |
| High-risk content (deportation, criminal) | Escalation message |

### Output
```json
{
  "approved": true,
  "modifications": [],
  "confidence_level": "high|medium|review_recommended"
}
```

---

## ADK Callbacks

**Directory**: `agents/callbacks/`

| Callback | Trigger | Action |
|----------|---------|--------|
| `pii_guard` | Before model call | Scan input for leaked PII patterns |
| `schema_validator` | After agent response | Validate against JSON schema |
| `disclaimer_injector` | Before user output | Append legal disclaimer |

---

## Prompt Files

**Directory**: `agents/prompts/`

| File | Agent |
|------|-------|
| `orchestrator.yaml` | Orchestrator |
| `intake.yaml` | Intake |
| `classifier.yaml` | Classifier |
| `extraction.yaml` | Extraction |
| `jobcenter.yaml` | Jobcenter Specialist |
| `auslaenderbehoerde.yaml` | Ausländerbehörde Specialist |
| `finanzamt.yaml` | Finanzamt Specialist |
| `krankenkasse.yaml` | Krankenkasse Specialist |
| `generic_gov.yaml` | Generic Specialist |
| `explainer.yaml` | Explainer |
| `action_planner.yaml` | Action Planner |
| `safety.yaml` | Safety Gate |

---

## Session Lifecycle

```
CREATE session → UPLOAD document → START analysis
  → PIPELINE (intake..safety) → STORE results
  → FOLLOW_UP chat (context from session)
  → DELETE (GDPR) or EXPIRE (retention)
```

Implementation entry point: `agents/root_orchestrator.py:create_root_agent()`
