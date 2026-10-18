# PlantPulse Central Server — DWSIM adapter contract

This server listens only on 127.0.0.1:8770. Start PlantPulse-Central.exe and keep it open.

## Fast continuous connection for the Pump–Tank flowsheet

A DWSIM Script Manager connector is available at:
`dwsim/PlantPulse_Continuous_Connector.py`

It is designed for the user's steady-state `Tank system.dwxmz` flowsheet and known object tags:
- Feed material stream: `PUMP`
- Pump: `PUMP-1`
- Discharge material stream: `2`
- Tank: `TANK-1`
- Energy stream: `E1`

### Setup

1. Start `PlantPulse-Central.exe` and wait for the dashboard to open at `http://127.0.0.1:8770`.
2. Open `Tank system.dwxmz` in DWSIM.
3. Open Script Manager and create/open an IronPython script.
4. Paste the contents of `dwsim/PlantPulse_Continuous_Connector.py` and run it once.
5. Keep DWSIM and PlantPulse-Central.exe open. The connector attempts to publish a snapshot immediately and then every 2 seconds.
6. Confirm that the dashboard changes to **DWSIM DATA RECEIVED** and check the last-seen age.

If the connector prints an error in DWSIM, copy the exact error text for troubleshooting. The connector depends on the DWSIM Script Manager exposing the global `Flowsheet` object and on the installed DWSIM build's object property names; it has not been verified on every DWSIM build.

## Telemetry contract

- `POST http://127.0.0.1:8770/api/telemetry/pumptank`
- `POST http://127.0.0.1:8770/api/telemetry/hx1`

The dashboard polls the central API every four seconds. The connector is intended to post new snapshots every two seconds, so displayed values should update within a few seconds after successful reads/posts.

The current steady-state model does not provide a changing liquid level. `vessel_volume_m3` is tank vessel volume, not measured liquid level. Residence time is estimated from vessel volume divided by feed volumetric flow; it is not a dynamic tank-level model.

## API

- `GET /api/health` — server health
- `GET /api/processes` — process registry and connection state
- `GET /api/process/hx1/telemetry`
- `GET /api/process/pumptank/telemetry`
- `POST /api/telemetry/{hx1|pumptank}` — publish telemetry
- `POST /api/process/{hx1|pumptank}/setpoints` — queue local setpoints

Setpoints are only queued in memory; they are **not** applied to DWSIM. This is a local dashboard/telemetry connector, not a safety system or live plant controller.
