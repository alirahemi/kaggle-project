"""Letter analysis router with stub pipeline responses."""

import asyncio
import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from apps.api_gateway.middleware.auth import get_current_user_id
from apps.api_gateway.schemas.analysis import (
    ActionItem,
    ActionPlan,
    AnalysisResult,
    AnalysisStatusResponse,
    ConfirmAnalysisRequest,
    DeadlineItem,
    Explanation,
    LetterExtraction,
    StartAnalysisRequest,
)
from apps.api_gateway.schemas.common import (
    AnalysisStatusEnum,
    AuthorityEnum,
    ConfidenceLevelEnum,
    LetterTypeEnum,
)
from config.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

_analyses: dict[UUID, AnalysisResult] = {}
_analysis_sessions: dict[UUID, UUID] = {}


def _load_sample_extraction() -> LetterExtraction:
    fixture = Path("tests/fixtures/expected_outputs/jobcenter_analysis.json")
    if fixture.exists():
        data = json.loads(fixture.read_text(encoding="utf-8"))
        extraction = data.get("extraction")
        if extraction:
            return LetterExtraction.model_validate(extraction)

    return LetterExtraction(
        deadlines=[
            DeadlineItem(
                date=date(2025, 7, 15),
                description="Submit requested documents",
                consequence_hint="Benefits may be reduced or stopped",
            )
        ],
        actions_required=[],
        references=[],
        confidence=0.82,
        case_number="JC-2025-001234",
    )


def _build_completed_result(analysis_id: UUID) -> AnalysisResult:
    extraction = _load_sample_extraction()
    return AnalysisResult(
        analysis_id=analysis_id,
        status=AnalysisStatusEnum.COMPLETED,
        authority=AuthorityEnum.JOBCENTER,
        letter_type=LetterTypeEnum.NACHFORDERUNG,
        confidence=extraction.confidence,
        confidence_level=ConfidenceLevelEnum.HIGH,
        extraction=extraction,
        explanation=Explanation(
            summary="The Jobcenter requests additional documents within two weeks.",
            key_points=[
                "Respond before the stated deadline.",
                "Include proof of residence and income.",
            ],
            locale="en",
        ),
        action_plan=ActionPlan(
            urgent=[
                ActionItem(
                    action="Gather Meldebescheinigung and bank statements",
                    deadline=date(2025, 7, 15),
                )
            ]
        ),
        disclaimer=(
            "AI-generated summary — not legal advice. Verify against the original letter."
        ),
        requires_review=False,
        completed_at=datetime.now(UTC),
    )


@router.post("", response_model=AnalysisStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    body: StartAnalysisRequest,
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> AnalysisStatusResponse:
    analysis_id = uuid4()
    result = _build_completed_result(analysis_id)
    _analyses[analysis_id] = result
    _analysis_sessions[analysis_id] = body.session_id

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        session_id=body.session_id,
        status=AnalysisStatusEnum.PROCESSING,
        pipeline_stage="intake",
    )


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(
    analysis_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> AnalysisResult:
    result = _analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return result


@router.get("/{analysis_id}/stream")
async def stream_analysis(
    analysis_id: UUID,
    user_id: str = Depends(get_current_user_id),
):
    if analysis_id not in _analyses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    async def event_generator():
        chunks = [
            "Analyzing letter structure…",
            "Identifying authority: Jobcenter.",
            "Extracting deadlines and required actions.",
            "Preparing plain-language explanation.",
        ]
        for chunk in chunks:
            yield {"event": "message", "data": chunk}
            await asyncio.sleep(0.3)
        yield {"event": "done", "data": "complete"}

    return EventSourceResponse(event_generator())


@router.post("/{analysis_id}/confirm", response_model=AnalysisStatusResponse)
async def confirm_analysis(
    analysis_id: UUID,
    body: ConfirmAnalysisRequest,
    user_id: str = Depends(get_current_user_id),
) -> AnalysisStatusResponse:
    result = _analyses.get(analysis_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    updated = result.model_copy(
        update={
            "authority": body.authority,
            "letter_type": body.letter_type or result.letter_type,
            "status": AnalysisStatusEnum.PROCESSING,
        }
    )
    _analyses[analysis_id] = updated
    session_id = _analysis_sessions.get(analysis_id, uuid4())

    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        session_id=session_id,
        status=AnalysisStatusEnum.PROCESSING,
        pipeline_stage="domain_specialist",
    )
