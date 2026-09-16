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
