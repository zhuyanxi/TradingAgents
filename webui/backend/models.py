from pydantic import BaseModel, Field
from typing import List, Optional


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    analysis_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    analysts: List[str] = Field(..., min_length=1)
    research_depth: int = Field(..., ge=1, le=5)
    llm_provider: str
    backend_url: str
    shallow_thinker: str
    deep_thinker: str
    google_thinking_level: Optional[str] = None
    openai_reasoning_effort: Optional[str] = None
    anthropic_effort: Optional[str] = None
