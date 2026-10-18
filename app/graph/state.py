"""LangGraph state schemas."""

from __future__ import annotations

import operator
from typing import Annotated

from typing_extensions import NotRequired, TypedDict

from app.models import (
    ConsultingResponse,
    Domain,
    Evidence,
    RoutingDecision,
    SpecialistReport,
    VerificationResult,
)


class ConsultingState(TypedDict):
    request_id: str
    question: str
    reports: Annotated[list[SpecialistReport], operator.add]
    evidence_packets: Annotated[list[Evidence], operator.add]
    errors: Annotated[list[str], operator.add]
    route: NotRequired[RoutingDecision]
    clarification_status: NotRequired[str]
    verification: NotRequired[VerificationResult]
    final_response: NotRequired[ConsultingResponse]
    retry_count: NotRequired[int]
    timing_metrics_ms: NotRequired[dict[str, float]]


class SpecialistTask(TypedDict):
    request_id: str
    question: str
    domain: Domain
