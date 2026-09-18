# FleetPulse

Real-time vehicle fleet telemetry and OTA update orchestration platform, with an LLM-powered diagnostics copilot.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-teal)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

FleetPulse simulates a fleet of connected vehicles streaming live telemetry (speed, battery, GPS, fault codes) and manages staged over-the-air (OTA) software rollouts across the fleet, similar to systems used by Tesla, Ford, and other automotive companies for fleet management and vehicle software delivery.

## Features

- **Real-time telemetry ingestion** via WebSockets, simulating hundreds of vehicles streaming live data
- **Staged OTA rollout engine** with canary batches, rollout percentage control, and automatic rollback on failure spikes
- **Live fleet dashboard** with map view, battery/fault alerts, and rollout progress tracking
- **AI diagnostics copilot** that explains fault codes and telemetry anomalies in plain language using an LLM

## Architecture

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│ Vehicle Simulator│ ──────────────────▶│ Telemetry Service │
└─────────────────┘                     └────────┬─────────┘
                                                  │ pub/sub
                                          ┌───────▼────────┐
                                          │      Redis      │
                                          └───────┬────────┘
                                                  │
                        ┌─────────────────────────┼─────────────────────────┐
                        ▼                                                   ▼
              ┌──────────────────┐                                ┌──────────────────┐
              │   OTA Service     │                                │ Diagnostics Copilot│
              │ (rollout logic)   │                                │      (LLM)         │
              └────────┬─────────┘                                └────────┬───────────┘
                       │                                                    │
                       ▼                                                    ▼
                ┌─────────────┐                                    ┌───────────────┐
                │  PostgreSQL  │                                    │  React Dashboard│
                └─────────────┘                                    └───────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11 |
| Real-time | WebSockets, Redis pub/sub |
| Database | PostgreSQL (Neon/Supabase) |
| Frontend | React, TypeScript |
| AI | LangChain + Groq/Ollama |
| Deployment | Render, Vercel |
| Containerization | Docker, Docker Compose |

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### Setup

```bash
git clone https://github.com/Vikram739/fleetpulse.git
cd fleetpulse
docker-compose up --build
```

Frontend: `http://localhost:3000`
API docs: `http://localhost:8000/docs`

### Environment Variables

```
DATABASE_URL=
REDIS_URL=
LLM_API_KEY=
```

## Running Services Standalone

### telemetry-service

Requires Redis running locally (or reachable at REDIS_URL).

```bash
cd telemetry-service
python -m venv .venv
.venv/Scripts/activate   # on Windows; use .venv/bin/activate on macOS or Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Run the tests:

```bash
pytest
```

Check it works:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/fleet
```

Connect a WebSocket client to `ws://localhost:8000/ws/telemetry` and send JSON matching:

```json
{"vehicle_id": "veh-1", "speed": 42, "battery_percent": 88, "latitude": 37.77, "longitude": -122.41, "fault_code": null, "firmware_version": "1.0.0"}
```

If Redis is not running, the service still starts and `/health` reports `"status": "degraded"` instead of crashing.

### vehicle-simulator

Requires telemetry-service running (locally or via docker-compose).

```bash
cd vehicle-simulator
python -m venv .venv
.venv/Scripts/activate   # on Windows; use .venv/bin/activate on macOS or Linux
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

Run the tests:

```bash
pytest
```

By default it simulates 25 vehicles sending telemetry every 1 to 3 seconds to `ws://localhost:8000/ws/telemetry`. Override `VEHICLE_COUNT`, `MIN_UPDATE_INTERVAL_SECONDS`, `MAX_UPDATE_INTERVAL_SECONDS`, or `TELEMETRY_WS_URL` as needed. If telemetry-service is unreachable, each vehicle logs a warning and retries with exponential backoff instead of crashing.

### ota-service

Requires Postgres running locally (or reachable at DATABASE_URL). Schema is applied automatically on startup, there is no manual migration step.

```bash
cd ota-service
python -m venv .venv
.venv/Scripts/activate   # on Windows; use .venv/bin/activate on macOS or Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

Run the tests (these test the rollout and validation logic directly, they do not require Postgres):

```bash
pytest
```

Try a full rollout by hand:

```bash
curl -X POST http://localhost:8001/firmware-versions -H "Content-Type: application/json" -d "{\"version\": \"1.2.0\"}"
curl -X POST http://localhost:8001/vehicles -H "Content-Type: application/json" -d "{\"vehicle_id\": \"veh-001\"}"
curl -X POST http://localhost:8001/rollouts -H "Content-Type: application/json" -d "{\"firmware_version\": \"1.2.0\"}"
curl -X POST http://localhost:8001/rollouts/1/advance
curl http://localhost:8001/rollouts/1
```

A rollout steps through its stages (10 percent, 50 percent, 100 percent by default) one `advance` call at a time. Each advance assigns the next batch of vehicles and simulates an outcome per vehicle (success, failed, or unresponsive). If the failure rate in a batch exceeds `failure_threshold_percent` (default 15), the rollout halts and every vehicle not yet touched is marked `rollback`. Use `POST /rollouts/{id}/rollback` to trigger a rollback manually at any time. If Postgres is not running, the service still starts and returns a 503 with a clear message instead of crashing.

### diagnostics-copilot

Requires Redis running locally. Uses Groq's free tier API if `GROQ_API_KEY` is set, otherwise falls back to a local Ollama model.

```bash
cd diagnostics-copilot
python -m venv .venv
.venv/Scripts/activate   # on Windows; use .venv/bin/activate on macOS or Linux
pip install -r requirements.txt
cp .env.example .env
# edit .env and set GROQ_API_KEY, or leave blank and run Ollama locally
uvicorn app.main:app --reload --port 8002
```

Run the tests (these test prompt building, output parsing, and validation directly, they do not call a real LLM or require Redis):

```bash
pytest
```

Try it:

```bash
curl -X POST http://localhost:8002/diagnose -H "Content-Type: application/json" -d "{\"fault_code\": \"P0171\", \"telemetry_context\": {\"speed\": 42, \"battery_percent\": 88}}"
```

Repeated calls for the same fault code are served from Redis instead of calling the LLM again. If the LLM call fails or times out, or if Redis is unreachable, the endpoint still returns a 200 response with a generic explanation instead of crashing or returning a stack trace. Invalid or blank fault codes return a 422 with a clear message. API keys are never logged or included in any response.

### dashboard

A React and TypeScript app (Vite, strict mode). Needs telemetry-service running to show live data, and ota-service and diagnostics-copilot for the rollout panel and fault explanations to work, but it will not crash or show a blank page if any of them are unreachable.

```bash
cd dashboard
npm install
cp .env.example .env
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`). With no backend services running you will see a "connecting" banner and clear empty-state messages instead of a blank page. With telemetry-service and the simulator running, the fleet map (Leaflet with OpenStreetMap tiles, no API key needed) and vehicle list populate live; clicking a fault code badge calls diagnostics-copilot and shows the explanation.

Type-check and build:

```bash
npm run build
```

If you open the dashboard in multiple tabs, only one tab opens a WebSocket connection to telemetry-service (elected via the Web Locks API); the other tabs receive the same live data over a BroadcastChannel, so you will not get a connection storm. Browsers without Web Locks support (older Safari) fall back to one connection per tab.

## Project Structure

```
fleetpulse/
├── telemetry-service/     # FastAPI + WebSocket ingestion
├── ota-service/           # Rollout orchestration
├── diagnostics-copilot/   # LLM fault explanation service
├── dashboard/             # React + TS frontend
├── vehicle-simulator/     # Simulated fleet data generator
├── docker-compose.yml
└── README.md
```

## Demo

Live: [fleetpulse.vercel.app](#) *(will add link once deployed)*

## Roadmap

- [ ] Add geofencing alerts
- [ ] Multi-region fleet support
- [ ] Historical analytics dashboard

## License

MIT
