from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.sensor_data import SensorData
from app.schemas.sensor_data import SensorDataCreate, SensorDataOut, SystemStatus

router = APIRouter(tags=["Sensor Data"])


@router.post("/sensor-data", response_model=SensorDataOut, status_code=201)
def create_sensor_data(payload: SensorDataCreate, db: Session = Depends(get_db)):
    record = SensorData(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/latest-data", response_model=SensorDataOut)
def latest_data(db: Session = Depends(get_db)):
    record = db.query(SensorData).order_by(desc(SensorData.created_at)).first()
    if not record:
        raise HTTPException(status_code=404, detail="No sensor data available")
    return record


@router.get("/history", response_model=list[SensorDataOut])
def history(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    records = db.query(SensorData).order_by(desc(SensorData.created_at)).limit(limit).all()
    return list(reversed(records))


@router.get("/system-status", response_model=SystemStatus)
def system_status(db: Session = Depends(get_db)):
    latest = db.query(SensorData).order_by(desc(SensorData.created_at)).first()
    return SystemStatus(
        sensor_health="online" if latest else "waiting-for-first-reading",
        wifi_status="reported-by-esp32-api-link",
        last_update_time=latest.created_at if latest else None,
        simulated_values=["nitrogen", "phosphorus", "potassium"],
        real_values=["temperature", "humidity", "soil_moisture", "pump_status"],
    )
