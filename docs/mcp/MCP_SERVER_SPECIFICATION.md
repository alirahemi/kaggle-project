# MCP Server Specification

> Model Context Protocol servers for the German Bureaucracy AI Agent  
> Transport: **stdio** (local) · **SSE** (production)  
> Auth: Bearer token via `MCP_AUTH_TOKEN`

## Server Registry

| Server | Module | Version | Tools | Resources |
|--------|--------|---------|-------|-----------|
| Document | `mcp_servers.document_mcp` | 1.0.0 | 5 | 1 |
| RAG | `mcp_servers.rag_mcp` | 1.0.0 | 3 | 2 |
| Gov Resources | `mcp_servers.gov_resources_mcp` | 1.0.0 | 3 | 1 |
| Calendar | `mcp_servers.calendar_mcp` | 1.0.0 | 3 | 0 |
| Audit | `mcp_servers.audit_mcp` | 1.0.0 | 4 | 0 |

Configuration: `config/mcp_servers.yaml`

---

## Server 1: bureaucracy-document-mcp

**Module**: `mcp_servers/document_mcp/server.py`

### Tools

#### `parse_document`
Parse PDF or plain text into structured content.

```json
// Input
{
  "file_path": "string",
  "max_pages": 20
}
// Output
{
  "text": "string",
  "page_count": 2,
  "metadata": {"title": "string|null"}
}
```

#### `ocr_document`
OCR for scanned PDFs and images.

```json
// Input
{
  "file_path": "string",
  "language": "deu"
}
// Output
{
  "text": "string",
  "confidence": 0.95
}
```

#### `redact_pii`
Redact names, addresses, Steuer-ID, Aktenzeichen patterns.

```json
// Input
{
  "text": "string",
  "preserve_aktenzeichen": false
}
// Output
{
  "redacted_text": "string",
  "redaction_map": {"[NAME_1]": "hash"},
  "pii_found": true
}
```

#### `store_document`
Encrypt and store document. Returns opaque `doc_id`.

```json
// Input
{
  "file_path": "string",
  "user_id": "uuid",
  "content_type": "application/pdf"
}
// Output
{
  "doc_id": "uuid",
  "storage_key": "string",
  "retention_expires_at": "ISO8601"
}
```

#### `get_document_text`
Retrieve document text (role-gated).

```json
// Input
{
  "doc_id": "uuid",
  "redacted_only": true
}
// Output
{
  "text": "string",
  "doc_id": "uuid"
}
```

### Resources
- `document://{doc_id}/metadata` — Document metadata without content

---

## Server 2: bureaucracy-rag-mcp

**Module**: `mcp_servers/rag_mcp/server.py`

### Tools

#### `search_knowledge`
Hybrid semantic + keyword search over curated corpus.

```json
// Input
{
  "query": "string",
  "authority": "jobcenter|null",
  "limit": 5
}
// Output
{
  "results": [
    {"title": "string", "content": "string", "source": "string", "score": 0.89}
  ]
}
```

#### `get_glossary_term`
Lookup bilingual glossary entry.

```json
// Input
{"term": "Bescheid", "locale": "en"}
// Output
{
  "term": "Bescheid",
  "definition_de": "string",
  "definition_en": "string",
  "related_terms": ["Widerspruch"]
}
```

#### `find_similar_cases`
Embedding search on synthetic letter templates.

```json
// Input
{
  "text_snippet": "string",
  "limit": 3
}
// Output
{
  "matches": [
    {"template_id": "string", "authority": "jobcenter", "letter_type": "nachforderung", "score": 0.91}
  ]
}
```

### Resources
- `knowledge://glossary/{term}`
- `knowledge://authority/{name}/faq`

---

## Server 3: bureaucracy-gov-resources-mcp

**Module**: `mcp_servers/gov_resources_mcp/server.py`

### Tools

#### `resolve_form`
Map action to official form ID and URL (curated catalog only).

```json
// Input
{
  "authority": "finanzamt",
  "action": "einspruch_einlegen"
}
// Output
{
  "form_id": "Einspruch",
  "name": "string",
  "url": "https://...",
  "notes": "string"
}
```

#### `get_authority_contact`
Public contact patterns for an authority type.

```json
// Input
{"authority": "auslaenderbehoerde", "bundesland": "BE"}
// Output
{
  "general_info_url": "https://...",
  "appointment_hint": "string",
  "phone_pattern": "string|null"
}
```

#### `list_required_documents`
Checklist template for letter type.

```json
// Input
{
  "authority": "jobcenter",
  "letter_type": "nachforderung"
}
// Output
{
  "documents": [
    {"name": "Gehaltsabrechnung", "description": "string", "required": true}
  ]
}
```

#### `get_official_links`
Curated official resource links.

```json
// Input
{"authority": "krankenkasse", "topic": "familienversicherung"}
// Output
{"links": [{"title": "string", "url": "https://..."}]}
```

### Resources
- `gov://forms/catalog` — Full form catalog JSON

---

## Server 4: bureaucracy-calendar-mcp

**Module**: `mcp_servers/calendar_mcp/server.py`

### Tools

#### `parse_german_date`
Resolve German date expressions to ISO.

```json
// Input
{
  "expression": "bis zum 15. des Folgemonats",
  "reference_date": "2026-03-01"
}
// Output
{
  "iso_date": "2026-04-15",
  "parsed": true,
  "original": "bis zum 15. des Folgemonats"
}
```

#### `business_days_until`
Count business days until deadline (Bundesland-aware).

```json
// Input
{
  "target_date": "2026-04-15",
  "bundesland": "BE",
  "from_date": "2026-03-22"
}
// Output
{
  "business_days": 17,
  "calendar_days": 24,
  "is_past": false
}
```

#### `urgency_score`
Compute priority score 0–100.

```json
// Input
{
  "deadline": "2026-04-15",
  "consequence_severity": "high|medium|low",
  "bundesland": "BE"
}
// Output
{
  "score": 85,
  "tier": "urgent"
}
```

---

## Server 5: bureaucracy-audit-mcp

**Module**: `mcp_servers/audit_mcp/server.py`

### Tools

#### `log_interaction`
Log agent step without PII.

```json
// Input
{
  "session_id": "uuid",
  "agent_name": "classifier",
  "tool_name": "search_knowledge|null",
  "duration_ms": 450,
  "outcome": "success|error"
}
// Output
{"event_id": "uuid"}
```

#### `get_session_summary`
Retrieve session audit trail.

```json
// Input
{"session_id": "uuid"}
// Output
{
  "events": [{"agent_name": "string", "timestamp": "ISO", "outcome": "string"}]
}
```

#### `export_user_data`
GDPR Art. 15 data export.

```json
// Input
{"user_id": "uuid"}
// Output
{"export_url": "string", "expires_at": "ISO"}
```

#### `delete_user_data`
GDPR Art. 17 erasure.

```json
// Input
{"user_id": "uuid", "confirm": true}
// Output
{"deleted": true, "documents_removed": 3, "sessions_removed": 5}
```

---

## MCP Manifest Format

Each server exposes `mcp_servers/{name}/manifest.json`:

```json
{
  "name": "bureaucracy-document-mcp",
  "version": "1.0.0",
  "description": "Document parsing, OCR, PII redaction, storage",
  "transport": "stdio",
  "tools": ["parse_document", "ocr_document", "redact_pii", "store_document", "get_document_text"]
}
```

---

## ADK Integration

**Adapter**: `agents/tools/mcp_tool_adapter.py`

```python
# Wraps MCP tools as ADK FunctionTool instances
# Loads server config from config/mcp_servers.yaml
# Spawns stdio subprocess per invocation (or connection pool in prod)
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| `MCP_AUTH_FAILED` | Invalid bearer token |
| `MCP_TOOL_NOT_FOUND` | Unknown tool name |
| `MCP_VALIDATION_ERROR` | Input schema validation failed |
| `MCP_STORAGE_ERROR` | Document storage failure |
| `MCP_RATE_LIMITED` | Too many requests |

---

## Security

- All servers validate `Authorization: Bearer {MCP_AUTH_TOKEN}`
- Document server never logs raw text
- Audit server never stores letter content
- RAG corpus contains no real user data
