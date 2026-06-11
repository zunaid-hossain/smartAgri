# SmartAgri Backend

FastAPI backend for the AI-Powered Smart Agriculture Monitoring & Auto Irrigation System.

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

## API

- `GET /` health and metadata
- `POST /sensor-data` save ESP32 readings
- `GET /sensor-data/stream` real-time sensor reading stream for the dashboard
- `GET /sensor-data/live` latest reading or wait for the next reading
- `GET /latest-data` latest reading
- `GET /history?limit=100` historical readings
- `GET /ai-recommendation` generate and store Bangla Gemini recommendation
- `GET /ai-recommendations?limit=20` previous stored AI recommendations
- `POST /ai-chat` general Bangla AI chat with optional latest sensor context
- `GET /system-status` dashboard status data

## Render

Use the backend directory as the root directory.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```
