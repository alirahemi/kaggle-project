# Complete Project Folder Tree

```
kaggle-project/
├── .env.example                          # Environment template (copy to .env)
├── .gitignore
├── DISCLAIMER.md                           # Legal disclaimer (DE/EN)
├── LICENSE                                 # Apache 2.0
├── README.md                               # Project overview & quick start
├── docker-compose.yml                      # Full stack orchestration
├── pyproject.toml                          # Python project config (ruff, pytest)
├── requirements.txt                        # Python 3.12 dependencies
│
├── agents/                                 # Google ADK multi-agent system
│   ├── __init__.py
│   ├── root_orchestrator.py                # Root LlmAgent pipeline
│   ├── intake_agent.py
│   ├── classifier_agent.py
│   ├── extraction_agent.py
│   ├── explainer_agent.py
│   ├── action_planner_agent.py
│   ├── safety_agent.py
│   ├── callbacks/
│   │   ├── __init__.py
│   │   ├── pii_guard.py
│   │   ├── schema_validator.py
│   │   └── disclaimer_injector.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── mcp_tool_adapter.py             # MCP → ADK FunctionTool
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── orchestrator.yaml
│   │   ├── intake.yaml
│   │   ├── classifier.yaml
│   │   ├── extraction.yaml
│   │   ├── explainer.yaml
│   │   ├── action_planner.yaml
│   │   ├── safety.yaml
│   │   ├── jobcenter.yaml
│   │   ├── auslaenderbehoerde.yaml
│   │   ├── finanzamt.yaml
│   │   ├── krankenkasse.yaml
│   │   └── generic_gov.yaml
│   └── specialists/
│       ├── __init__.py
│       ├── base.py
│       ├── jobcenter_agent.py
│       ├── auslaenderbehoerde_agent.py
│       ├── finanzamt_agent.py
│       ├── krankenkasse_agent.py
│       └── generic_gov_agent.py
│
├── apps/
│   ├── __init__.py
│   ├── api_gateway/                        # FastAPI REST + SSE
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── rate_limit.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── auth.py
│   │   │   ├── sessions.py
│   │   │   ├── documents.py
│   │   │   ├── analysis.py
│   │   │   ├── chat.py
│   │   │   └── users.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── common.py
│   │       ├── session.py
│   │       ├── document.py
│   │       ├── analysis.py
│   │       └── chat.py
│   └── streamlit_app/                        # Concierge UI
│       ├── __init__.py
│       ├── app.py
│       ├── .streamlit/
│       │   ├── config.toml
│       │   └── secrets.toml.example
│       ├── pages/
│       │   ├── 01_analyze_letter.py
│       │   ├── 02_action_plan.py
│       │   ├── 03_ask_concierge.py
│       │   └── 04_privacy_settings.py
│       ├── components/
│       │   ├── __init__.py
│       │   ├── upload.py
│       │   ├── deadline_card.py
│       │   └── disclaimer_banner.py
│       └── client/
│           ├── __init__.py
│           └── api_client.py
│
├── config/                                 # Application configuration
│   ├── __init__.py
│   ├── settings.py                         # Pydantic settings from .env
│   ├── agents.yaml                         # ADK agent registry
│   ├── mcp_servers.yaml                    # MCP server registry
│   ├── logging.yaml
│   └── schemas/
│       └── letter_extraction.json          # JSON schema for extraction agent
│
├── data/
│   ├── storage/.gitkeep                    # Encrypted document storage
│   └── uploads/.gitkeep                    # Temporary upload buffer
│
├── db/
│   ├── __init__.py
│   ├── models.py                           # SQLAlchemy ORM models
│   ├── alembic.ini
│   └── migrations/
│       └── 001_initial.sql
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── security.md
│   ├── demo_script.md
│   ├── kaggle_submission.md
│   ├── PROJECT_STRUCTURE.md                # This file
│   ├── agents/
│   │   └── AGENT_SPECIFICATIONS.md
│   ├── api/
│   │   ├── CONTRACTS.md
│   │   └── openapi.yaml
│   └── mcp/
│       └── MCP_SERVER_SPECIFICATION.md
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.streamlit
│   │   ├── Dockerfile.mcp
│   │   └── Dockerfile.adk
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── cloud_run.tf
│       ├── cloud_sql.tf
│       ├── iam.tf
│       └── terraform.tfvars.example
│
├── knowledge/                              # Curated RAG corpus (no user data)
│   ├── glossary/
│   │   └── terms.json
│   ├── forms/
│   │   └── catalog.json
│   ├── authorities/
│   │   ├── jobcenter/faq.md
│   │   ├── auslaenderbehoerde/faq.md
│   │   ├── finanzamt/faq.md
│   │   └── krankenkasse/faq.md
│   └── letter_templates/
│       └── jobcenter_nachforderung.json
│
├── mcp_servers/                            # Model Context Protocol tool servers
│   ├── __init__.py
│   ├── document_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── manifest.json
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── parser.py
│   │       ├── pii.py
│   │       └── storage.py
│   ├── rag_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   └── manifest.json
│   ├── gov_resources_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── manifest.json
│   │   └── catalog/
│   │       └── forms.json
│   ├── calendar_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── manifest.json
│   │   └── holidays_de.json
│   └── audit_mcp/
│       ├── __init__.py
│       ├── server.py
│       └── manifest.json
│
├── scripts/
│   ├── run_local.sh
│   ├── run_local.ps1
│   ├── ingest_knowledge.py
│   └── seed_synthetic_letters.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── test_config.py
    │   └── test_calendar_mcp.py
    ├── integration/
    │   ├── test_api_health.py
    │   └── test_mcp_tools.py
    └── fixtures/
        ├── sample_letters/
        │   ├── jobcenter_nachforderung.txt
        │   └── finanzamt_bescheid.txt
        └── expected_outputs/
            └── jobcenter_analysis.json
```

**Total**: ~160+ files across 10 top-level directories.
