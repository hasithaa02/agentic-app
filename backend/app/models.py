from pydantic import BaseModel
from typing import Optional, List, Any

class IngestResponse(BaseModel):
    ingestion_id: str
    extracted_text: str
    metadata: dict
    clarifying_question: Optional[str] = None

class IntentResult(BaseModel):
    intent: str
    confidence: float
    clarifying_question: Optional[str] = None
    required_constraints: Optional[dict] = None

class PlanStep(BaseModel):
    task: str
    reason: str
    params: Optional[dict] = None

class ExecuteResponse(BaseModel):
    results: dict
    logs: List[str]
