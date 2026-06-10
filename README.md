# AI-Powered Smart Agriculture Monitoring & Auto Irrigation System

Production-ready full-stack IoT platform for ESP32-based crop monitoring, relay-controlled auto irrigation, historical analytics, and Bangla AI recommendations with Gemini.

## Complete Folder Structure

```text
smartagri/
├── backend/
│   ├── app/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── lib/
│   ├── package.json
│   ├── vercel.json
│   └── .env.example
├── esp32/
│   └── smart_agri_controller/
│       └── smart_agri_controller.ino
├── render.yaml
└── README.md
```

## System Architecture

ESP32 reads real DHT22 temperature, real DHT22 humidity, and real soil moisture. The NPK sensor is currently defective, so nitrogen, phosphorus, and potassium are generated as realistic simulated values. ESP32 applies the irrigation rule locally, controls the relay-driven water pump, displays live data on the 16x2 I2C LCD, and sends telemetry to FastAPI every 30 seconds.

FastAPI stores telemetry in PostgreSQL or Supabase through SQLAlchemy. React polls the API every 30 seconds and displays live status, charts, and Gemini-powered Bangla recommendations.

## Hardware Diagram

```text
ESP32 3V3  -> DHT22 VCC
ESP32 GND  -> DHT22 GND, Soil GND, Relay GND, LCD GND
ESP32 GPIO4 -> DHT22 DATA
ESP32 GPIO34 -> Soil Moisture AO
ESP32 GPIO26 -> Relay IN
ESP32 5V/VIN -> Relay VCC, LCD VCC
ESP32 GPIO21 -> LCD SDA
ESP32 GPIO22 -> LCD SCL

Relay COM -> Pump power positive
Relay NO  -> External pump supply positive
Pump negative -> External pump supply negative
```

Use an external pump power supply. Do not power a water pump directly from the ESP32.

## Sensor Data Separation

Real sensor values:

- Temperature
- Humidity
- Soil moisture
- Pump status

Simulated values because the NPK sensor is defective:

- Nitrogen: `20-80`
- Phosphorus: `5-45`
- Potassium: `20-100`

## Pump Logic

```python
if soil_moisture < 30:
    pump = ON
else:
    pump = OFF
```

## Database Schema

`SensorData`

```text
id, temperature, humidity, soil_moisture, nitrogen, phosphorus, potassium, pump_status, created_at
```

`AIRecommendation`

```text
id, recommendation, created_at
```

## API Documentation

Run the backend and open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Endpoints:

- `GET /`
- `POST /sensor-data`
- `GET /latest-data`
- `GET /history`
- `GET /ai-recommendation`
- `GET /system-status`

Example ESP32 payload:

```json
{
  "temperature": 29.4,
  "humidity": 71.2,
  "soil_moisture": 28,
  "nitrogen": 54,
  "phosphorus": 18,
  "potassium": 76,
  "pump_status": true
}
```

## ESP32 Setup

Install Arduino libraries:

- `DHT sensor library`
- `Adafruit Unified Sensor`
- `ArduinoJson`
- `LiquidCrystal_I2C`

Open `esp32/smart_agri_controller/smart_agri_controller.ino`, then set:

- `WIFI_SSID`
- `WIFI_PASSWORD`
- `API_URL`
- `DRY_ADC` and `WET_ADC` after calibrating your soil sensor

Upload the sketch to ESP32. The board sends data every 30 seconds.

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

For Supabase, set `DATABASE_URL` to the Supabase PostgreSQL connection string.

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to the FastAPI backend URL.

## Gemini Setup

Create a Gemini API key and set:

```bash
GEMINI_API_KEY=your_gemini_api_key
```

If no key is configured, the backend returns a Bangla fallback recommendation so the dashboard remains usable.

## Render Deployment Guide

This project follows Render's FastAPI deployment command style. Use `backend` as the root directory.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

- `DATABASE_URL`
- `GEMINI_API_KEY`
- `CORS_ORIGINS=https://your-frontend.vercel.app`
- `ENVIRONMENT=production`

You can also deploy with `render.yaml` from the repository root.

## Vercel Deployment Guide

Import the repository into Vercel, set the frontend root directory to `frontend`, and add:

```bash
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

The included `frontend/vercel.json` handles SPA routing.

## Netlify Deployment Guide

Netlify can host the React frontend for free. The included `netlify.toml` builds the `frontend` folder and publishes its `dist` output.

In Netlify, import the GitHub repository. Netlify will read `netlify.toml` from the repository root:

```text
Base directory: frontend
Build command: npm run build
Publish directory: dist
```

Add this environment variable:

```bash
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

The FastAPI backend still needs a server host such as Render because Netlify static hosting cannot run a persistent Python API service.

## GitHub Push Guide

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main
```

## Production Notes

- Use PostgreSQL or Supabase in production, not the local SQLite fallback.
- Add a secret token or device API key before exposing `/sensor-data` publicly.
- Use calibrated soil moisture ADC values for your specific sensor and soil.
- Keep the NPK simulated label visible until the physical NPK sensor is repaired.
