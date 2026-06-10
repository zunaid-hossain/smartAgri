from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.ai_recommendation import AIRecommendation
from app.models.sensor_data import SensorData
from app.schemas.ai_recommendation import AIRecommendationResponse
from app.services.gemini_service import generate_recommendation

router = APIRouter(tags=["AI Recommendation"])


@router.get("/ai-recommendation", response_model=AIRecommendationResponse)
def ai_recommendation(db: Session = Depends(get_db)):
    sensor_data = db.query(SensorData).order_by(desc(SensorData.created_at)).first()
    if not sensor_data:
        raise HTTPException(status_code=404, detail="No sensor data available")

    recommendation, source = generate_recommendation(sensor_data)
    saved = AIRecommendation(recommendation=recommendation)
    db.add(saved)
    db.commit()
    db.refresh(saved)

    return AIRecommendationResponse(
        recommendation=recommendation,
        source=source,
        saved=saved,
    )
