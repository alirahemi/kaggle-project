# API Contracts

> REST + SSE API for German Bureaucracy AI Agent  
> Base URL: `/api/v1`  
> OpenAPI: [openapi.yaml](./openapi.yaml)

## Authentication

All endpoints except `/health` require JWT Bearer token.

```
Authorization: Bearer <access_token>
```

Obtain token via `POST /api/v1/auth/token` (demo) or OAuth (production).

---

## Common Types

### ErrorResponse
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {}
  }
}
```

### AuthorityEnum
`jobcenter` | `auslaenderbehoerde` | `finanzamt` | `krankenkasse` | `other`

### LetterTypeEnum
`bewilligungsbescheid` | `ablehnungsbescheid` | `nachforderung` | `fristsetzung` | `termin` | `mahnung` | `bescheid` | `other`

---

## Endpoints

### Health

#### `GET /health`
No auth required.

**Response 200**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "up",
    "redis": "up",
    "gemini": "configured"
  }
}
```

---

### Auth

#### `POST /api/v1/auth/token`
Demo authentication.

**Request**
```json
{
  "user_id": "demo-user-uuid",
  "locale": "en"
}
```

**Response 200**
```json
{
  "access_token": "jwt...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### Sessions

#### `POST /api/v1/sessions`
Create analysis session.

**Request**
```json
{
  "locale": "en",
  "bundesland": "BE"
}
```

**Response 201**
```json
{
  "session_id": "uuid",
  "created_at": "2026-03-22T10:00:00Z",
  "locale": "en",
  "bundesland": "BE",
  "status": "active"
}
```

#### `GET /api/v1/sessions/{session_id}`
Retrieve session with latest analysis.

**Response 200**
```json
{
  "session_id": "uuid",
  "status": "active",
  "document_id": "uuid|null",
  "analysis_id": "uuid|null",
  "created_at": "ISO8601"
}
```

#### `DELETE /api/v1/sessions/{session_id}`
End session.

**Response 204** — No content

---

### Documents

#### `POST /api/v1/documents`
Upload official letter (multipart/form-data).

**Form fields**
- `file`: PDF, PNG, JPG, or TXT (max 20 MB)
- `session_id`: UUID (required)

**Response 201**
```json
{
  "document_id": "uuid",
  "session_id": "uuid",
  "filename": "letter.pdf",
  "content_type": "application/pdf",
  "page_count": 2,
  "redacted_preview": "First 500 chars...",
  "pii_redacted": true,
  "retention_expires_at": "ISO8601"
}
```

#### `GET /api/v1/documents/{document_id}`
Get document metadata.

**Response 200**
```json
{
  "document_id": "uuid",
  "filename": "letter.pdf",
  "page_count": 2,
  "status": "stored",
  "created_at": "ISO8601"
}
```

---

### Analysis

#### `POST /api/v1/analysis`
Start multi-agent letter analysis.

**Request**
```json
{
  "session_id": "uuid",
  "document_id": "uuid",
  "locale": "en",
  "confirm_authority": null
}
```

`confirm_authority` — optional user override when classifier confidence is low.

**Response 202**
```json
{
  "analysis_id": "uuid",
  "session_id": "uuid",
  "status": "processing",
  "pipeline_stage": "intake"
}
```

#### `GET /api/v1/analysis/{analysis_id}`
Get analysis result (poll until complete).

**Response 200**
```json
{
  "analysis_id": "uuid",
  "status": "completed",
  "authority": "jobcenter",
  "letter_type": "nachforderung",
  "confidence": 0.92,
  "confidence_level": "high",
  "extraction": { },
  "explanation": {
    "summary": "string",
    "key_points": ["string"],
    "glossary_terms": [],
    "locale": "en"
  },
  "action_plan": {
    "urgent": [],
    "this_week": [],
    "later": [],
    "optional": []
  },
  "disclaimer": "string",
  "requires_review": false,
  "completed_at": "ISO8601"
}
```

**Status values**: `processing` | `completed` | `failed` | `requires_confirmation`

#### `GET /api/v1/analysis/{analysis_id}/stream`
SSE stream for explanation phase.

**Headers**
```
Accept: text/event-stream
```

**Events**
```
event: stage
data: {"stage": "classifier", "message": "Identifying authority..."}

event: token
data: {"text": "This letter is a "}

event: complete
data: {"analysis_id": "uuid", "status": "completed"}
```

#### `POST /api/v1/analysis/{analysis_id}/confirm`
Confirm authority when classifier confidence is low.

**Request**
```json
{
  "authority": "jobcenter",
  "letter_type": "nachforderung"
}
```

**Response 200** — Resumes pipeline, returns updated analysis status

---

### Chat (Concierge Follow-up)

#### `POST /api/v1/chat`
Follow-up question in session context.

**Request**
```json
{
  "session_id": "uuid",
  "message": "What happens if I miss this deadline?"
}
```

**Response 200**
```json
{
  "message_id": "uuid",
  "response": "string",
  "sources": ["extraction.deadlines[0]"],
  "disclaimer": "string"
}
```

---

### User Data (GDPR)

#### `GET /api/v1/users/me/data`
Export all user data.

**Response 200**
```json
{
  "export_id": "uuid",
  "download_url": "string",
  "expires_at": "ISO8601"
}
```

#### `DELETE /api/v1/users/me/data`
Delete all user data.

**Request**
```json
{
  "confirm": true
}
```

**Response 200**
```json
{
  "deleted": true,
  "documents_removed": 3,
  "sessions_removed": 5
}
```

---

## Webhook Events (Future)

| Event | Payload |
|-------|---------|
| `analysis.completed` | `{analysis_id, session_id, authority}` |
| `analysis.failed` | `{analysis_id, error_code}` |

---

## Rate Limits

- Default: 20 requests/minute per user
- Upload: 5 documents/minute
- Analysis: 3 concurrent per user

**Response 429**
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "retry_after": 30
  }
}
```
