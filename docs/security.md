# Security

## Data Classification

| Data | Classification | Storage | Retention |
|------|----------------|---------|-----------|
| Uploaded letters | Confidential PII | Encrypted object storage | 30 days default |
| Redacted text | Internal | Session state | Session lifetime |
| Analysis results | Internal | PostgreSQL | 90 days |
| Audit logs | Operational | PostgreSQL | 1 year (no content) |
| RAG corpus | Public/static | Vector DB | Indefinite |

## Controls

- **PII redaction** before LLM (`document_mcp.redact_pii`)
- **JWT** on all API endpoints
- **Bearer token** on MCP server invocations
- **Rate limiting** per IP/user (`RATE_LIMIT_PER_MINUTE`)
- **Upload limits** — 20 MB, 20 pages max
- **Gemini safety settings** enabled
- **Safety Agent** final gate before user output
- **GDPR** — export and delete via `audit_mcp`

## Production Checklist

- [ ] Rotate `APP_SECRET_KEY`, `JWT_SECRET_KEY`, `MCP_AUTH_TOKEN`
- [ ] Enable Vertex AI in `europe-west1`
- [ ] Configure Cloud SQL with private IP
- [ ] Enable GCS SSE-KMS encryption
- [ ] Disable `APP_DEBUG`
- [ ] Configure WAF / Cloud Armor
- [ ] Set up secret manager (no secrets in env files in prod)

## Disclaimer

All user-facing outputs include mandatory legal disclaimers. See [DISCLAIMER.md](../DISCLAIMER.md).
