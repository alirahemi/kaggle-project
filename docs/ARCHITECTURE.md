# Architecture

Production architecture for the German Bureaucracy AI Agent.

See the full principal-engineer design in the project README and the diagrams below.

## System Layers

1. **Presentation** — Streamlit concierge UI (upload, chat, action dashboard)
2. **Application** — FastAPI gateway (auth, rate limit, file upload, SSE)
3. **Agents** — Google ADK orchestrator + 8 specialized agents
4. **Tools** — 5 MCP servers (document, RAG, gov resources, calendar, audit)
5. **Data** — PostgreSQL, pgvector, encrypted object storage

## Agent Pipeline

```
Upload → Intake → Classifier → Extraction → Domain Specialist
         → Explainer → Action Planner → Safety Gate → Response
```

## Deployment

- **Local**: `docker compose up`
- **Production**: Cloud Run (EU) + Cloud SQL + GCS + Vertex AI

Configuration: `config/agents.yaml`, `config/mcp_servers.yaml`, `docker-compose.yml`
