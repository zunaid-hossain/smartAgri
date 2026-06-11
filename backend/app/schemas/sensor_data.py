from datetime import datetime

from pydantic import BaseModel, Field


class SensorDataCreate(BaseModel):
    temperature: float = Field(ge=-20, le=80, description="DHT11 temperature sensor value in Celsius")
    humidity: float = Field(ge=0, le=100, description="DHT11 humidity sensor value in percent")
    soil_moisture: float = Field(ge=0, le=100)
    nitrogen: float = Field(ge=20, le=80, description="NPK sensor value")
    phosphorus: float = Field(ge=5, le=45, description="NPK sensor value")
    potassium: float = Field(ge=20, le=100, description="NPK sensor value")
    pump_status: bool


class SensorDataOut(SensorDataCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemStatus(BaseModel):
    sensor_health: str
    wifi_status: str
    last_update_time: datetime | None
    seconds_since_last_update: int | None = None
    real_values: list[str]
