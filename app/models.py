from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date


class FieldData(BaseModel):
    value: Optional[Any]
    confidence: Optional[float]


class ProcessingInstructions(BaseModel):
    workflow: str
    confidence_threshold: float
    hitl_on_failure: bool


class ValidationResult(BaseModel):
    field: str
    valid: bool
    reason: Optional[str] = None


class Decision(BaseModel):
    route: Optional[str] = None


class AuditEntry(BaseModel):
    timestamp: str
    service: str
    action: str
    envelope_id: str
    result: str
    details: Dict[str, Any]

class MatchingResult(BaseModel):
    matched_code: Optional[str]
    match_confidence: float
    rationale: Optional[str]
    fallback_used: bool
    source: str
    
class Envelope(BaseModel):
    envelope_id: str
    extraction: Dict[str, FieldData]
    processing_instructions: ProcessingInstructions

    validation_results: Optional[List[ValidationResult]] = None
    decision: Optional[Decision] = None
    audit: List[AuditEntry] = Field(default_factory=list)
    matching_results: Optional[MatchingResult] = None

