from datetime import datetime

from pydantic import BaseModel, Field


class SensorDataCreate(BaseModel):
    temperature: float = Field(ge=-20, le=80)
    humidity: float = Field(ge=0, le=100)
    soil_moisture: float = Field(ge=0, le=100)
    nitrogen: float = Field(ge=20, le=80, description="Simulated NPK value")
    phosphorus: float = Field(ge=5, le=45, description="Simulated NPK value")
    potassium: float = Field(ge=20, le=100, description="Simulated NPK value")
    pump_status: bool


class SensorDataOut(SensorDataCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemStatus(BaseModel):
    sensor_health: str
    wifi_status: str
    last_update_time: datetime | None
    simulated_values: list[str]
    real_values: list[str]
