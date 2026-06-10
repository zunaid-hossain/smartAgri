from datetime import datetime

from pydantic import BaseModel


class AIRecommendationOut(BaseModel):
    id: int
    recommendation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AIRecommendationResponse(BaseModel):
    recommendation: str
    source: str
    saved: AIRecommendationOut | None = None
