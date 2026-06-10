from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import Base, engine
from app.models import AIRecommendation, SensorData
from app.routers import ai, sensor


settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="FastAPI backend for ESP32 smart agriculture monitoring and auto irrigation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI-Powered Smart Agriculture Monitoring API is running",
        "real_sensor_values": ["temperature", "humidity", "soil_moisture", "pump_status"],
        "simulated_values": ["nitrogen", "phosphorus", "potassium"],
    }


app.include_router(sensor.router)
app.include_router(ai.router)
