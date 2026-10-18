"""LangGraph state schemas."""
"""Defines the information traveling through LangGraph."""


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
    # Unique identifier for the request
    request_id: str
    # Original customer question
    question: str
    # Results from specialist agents, 
    # operator.add tells LangGraph to combine reports from parallel specialists rather than letting one specialist overwrite another.
    reports: Annotated[list[SpecialistReport], operator.add]
    # Retrieved document excerpts
    evidence_packets: Annotated[list[Evidence], operator.add]
    # Errors collected during execution
    errors: Annotated[list[str], operator.add]
    # Manager’s routing decision
    route: NotRequired[RoutingDecision]
    # Future clarification tracking
    clarification_status: NotRequired[str]
    # Evidence verification result
    verification: NotRequired[VerificationResult]
    # Final consulting answer
    final_response: NotRequired[ConsultingResponse]
    # Future retry tracking
    retry_count: NotRequired[int]
    # Future performance measurements
    timing_metrics_ms: NotRequired[dict[str, float]]

# smaller state sent to one specialist
class SpecialistTask(TypedDict):
    request_id: str
    question: str
    domain: Domain
