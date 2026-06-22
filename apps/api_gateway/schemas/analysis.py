"""Letter analysis schemas aligned with openapi.yaml."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api_gateway.schemas.common import (
    AnalysisStatusEnum,
    AuthorityEnum,
    ConfidenceLevelEnum,
    LetterTypeEnum,
)


class DeadlineItem(BaseModel):
    date: date
    description: str
    consequence_hint: str | None = None


class ActionRequiredItem(BaseModel):
    verb: str
    object: str
    mandatory: bool


class ReferenceItem(BaseModel):
    law: str | None = None
    section: str | None = None


class AmountItem(BaseModel):
    value: float
    currency: str = "EUR"
    context: str | None = None


class LetterExtraction(BaseModel):
    deadlines: list[DeadlineItem] = Field(default_factory=list)
    actions_required: list[ActionRequiredItem] = Field(default_factory=list)
    references: list[ReferenceItem] = Field(default_factory=list)
    amounts: list[AmountItem] = Field(default_factory=list)
    case_number: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class GlossaryTerm(BaseModel):
    term: str
    definition: str


class Explanation(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    glossary_terms: list[GlossaryTerm] = Field(default_factory=list)
    locale: str = "en"


class ActionItem(BaseModel):
    action: str
    deadline: date | None = None
    form_url: str | None = None


class ActionPlan(BaseModel):
    urgent: list[ActionItem] = Field(default_factory=list)
    this_week: list[ActionItem] = Field(default_factory=list)
    later: list[ActionItem] = Field(default_factory=list)
    optional: list[ActionItem] = Field(default_factory=list)


class StartAnalysisRequest(BaseModel):
    session_id: UUID
    document_id: UUID
    locale: str | None = None
    confirm_authority: AuthorityEnum | None = None


class ConfirmAnalysisRequest(BaseModel):
    authority: AuthorityEnum
    letter_type: LetterTypeEnum | None = None


class AnalysisStatusResponse(BaseModel):
    analysis_id: UUID
    session_id: UUID
    status: AnalysisStatusEnum
    pipeline_stage: str


class AnalysisResult(BaseModel):
    analysis_id: UUID
    status: AnalysisStatusEnum
    authority: AuthorityEnum | None = None
    letter_type: LetterTypeEnum | None = None
    confidence: float | None = None
    confidence_level: ConfidenceLevelEnum | None = None
    extraction: LetterExtraction | None = None
    explanation: Explanation | None = None
    action_plan: ActionPlan | None = None
    disclaimer: str | None = None
    requires_review: bool = False
    completed_at: datetime | None = None
