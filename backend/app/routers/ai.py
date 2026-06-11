from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.ai_recommendation import AIRecommendation
from app.models.sensor_data import SensorData
from app.schemas.ai_recommendation import AIChatRequest, AIChatResponse, AIRecommendationOut, AIRecommendationResponse
from app.services.gemini_service import generate_chat_reply, generate_recommendation

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


@router.get("/ai-recommendations", response_model=list[AIRecommendationOut])
def ai_recommendation_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    recommendations = (
        db.query(AIRecommendation)
        .order_by(desc(AIRecommendation.created_at))
        .limit(limit)
        .all()
    )
    return recommendations


@router.post("/ai-chat", response_model=AIChatResponse)
def ai_chat(payload: AIChatRequest, db: Session = Depends(get_db)):
    sensor_data = db.query(SensorData).order_by(desc(SensorData.created_at)).first()
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    reply, source = generate_chat_reply(sensor_data, message)
    return AIChatResponse(reply=reply, source=source)
