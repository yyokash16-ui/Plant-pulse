# PlantPulse — DWSIM Digital Twin

PlantPulse is a local dashboard for multiple DWSIM process twins. The independent **Central Server** is the recommended starting point for upcoming process integrations; it does not require the old HX1 bridge on port 8765 or the previous server on port 8766.

## Start the central system on Windows

1. Install Python 3.10 or newer.
2. Download or clone this repository.
3. Double-click `start_central_server.bat`.
4. The dashboard opens at **http://127.0.0.1:8770**.
5. Keep that window open while using PlantPulse.

The new server runs independently on port 8770 and serves the existing dashboard. It supports a central process registry for HX1 and Pump–Tank, receives telemetry from DWSIM adapters, and reports stale/disconnected data. It binds to loopback only.

## Important integration status

The central server and one-click launcher have been added. The dashboard can run without finding or starting the old server. However, **real DWSIM data will appear only after a DWSIM-side adapter posts telemetry** to the central server. The central server does not guess object names or pretend local estimator values are DWSIM results.

Read [Central Server API and DWSIM adapter contract](docs/CENTRAL_SERVER.md) for the endpoints and payload formats.

## Features

- Central process registry with separate HX1 and Pump–Tank process IDs.
- Health, process connection status, telemetry timestamps, and stale-data detection.
- Steady-state Pump–Tank digital-twin page showing measured feed/discharge stream conditions, pump pressure rise/efficiency/head, tank vessel volume/residence time, and energy-stream duty.
- Explicit canonical telemetry keys and raw JSON diagnostics.
- Local-only API; no cloud service or remote listener required.

## Central API

- `GET http://127.0.0.1:8770/api/health`
- `GET http://127.0.0.1:8770/api/processes`
- `GET http://127.0.0.1:8770/api/process/hx1/telemetry`
- `GET http://127.0.0.1:8770/api/process/pumptank/telemetry`
- `POST http://127.0.0.1:8770/api/telemetry/hx1`
- `POST http://127.0.0.1:8770/api/telemetry/pumptank`

Setpoints can be queued through the API, but they are not written into DWSIM until a suitable in-process adapter reads them and applies the correct manipulated-variable property. Do not use this as live plant control or a safety system.

## Legacy mode

The older `start_plantpulse.bat` and `server.py` remain in the repository for the prior setup. They use port 8766 and proxy the existing bridge on port 8765. **For the new centralized architecture, use `start_central_server.bat` instead.**

## Troubleshooting

- If port 8770 is occupied, set `PLANTPULSE_CENTRAL_PORT` before starting `central_server.py`.
- Visit `http://127.0.0.1:8770/api/health` to verify the central server.
- If a process is disconnected, verify that its DWSIM adapter is posting telemetry every 1–5 seconds.
- GitHub Pages cannot run a local Python server or access a running DWSIM process.
