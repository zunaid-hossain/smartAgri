import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.sensor_data import SensorData
from app.schemas.sensor_data import SensorDataCreate, SensorDataOut, SystemStatus
from app.services.realtime import sensor_data_broadcaster

router = APIRouter(tags=["Sensor Data"])


@router.post("/sensor-data", response_model=SensorDataOut, status_code=201)
def create_sensor_data(payload: SensorDataCreate, db: Session = Depends(get_db)):
    record = SensorData(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    sensor_data_broadcaster.publish(SensorDataOut.model_validate(record).model_dump(mode="json"))
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


@router.get("/sensor-data/stream")
async def sensor_data_stream(request: Request):
    async def events():
        yield "event: connected\ndata: {\"status\":\"connected\"}\n\n"
        async for message in sensor_data_broadcaster.subscribe():
            if await request.is_disconnected():
                break
            yield f"event: sensor-data\ndata: {message}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sensor-data/live", response_model=SensorDataOut)
async def live_sensor_data(request: Request, db: Session = Depends(get_db)):
    latest = db.query(SensorData).order_by(desc(SensorData.created_at)).first()
    if latest:
        return latest

    async for message in sensor_data_broadcaster.subscribe():
        if await request.is_disconnected():
            break
        return SensorDataOut(**json.loads(message))

    raise HTTPException(status_code=404, detail="No sensor data available")


@router.get("/system-status", response_model=SystemStatus)
def system_status(db: Session = Depends(get_db)):
    latest = db.query(SensorData).order_by(desc(SensorData.created_at)).first()
    seconds_since_last_update = None
    sensor_health = "waiting-for-first-reading"
    if latest:
        latest_at = latest.created_at
        if latest_at.tzinfo is None:
            latest_at = latest_at.replace(tzinfo=timezone.utc)
        seconds_since_last_update = int((datetime.now(timezone.utc) - latest_at).total_seconds())
        sensor_health = "online" if seconds_since_last_update <= 90 else "stale"

    return SystemStatus(
        sensor_health=sensor_health,
        wifi_status="reported-by-esp32-api-link",
        last_update_time=latest.created_at if latest else None,
        seconds_since_last_update=seconds_since_last_update,
        real_values=["temperature", "humidity", "soil_moisture", "nitrogen", "phosphorus", "potassium", "pump_status"],
    )
