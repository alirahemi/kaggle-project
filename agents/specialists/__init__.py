"""Domain specialist agents for German government authorities."""

from agents.specialists.auslaenderbehoerde_agent import create_auslaenderbehoerde_agent
from agents.specialists.finanzamt_agent import create_finanzamt_agent
from agents.specialists.generic_gov_agent import create_generic_gov_agent
from agents.specialists.jobcenter_agent import create_jobcenter_agent
from agents.specialists.krankenkasse_agent import create_krankenkasse_agent

__all__ = [
    "create_auslaenderbehoerde_agent",
    "create_finanzamt_agent",
    "create_generic_gov_agent",
    "create_jobcenter_agent",
    "create_krankenkasse_agent",
]
