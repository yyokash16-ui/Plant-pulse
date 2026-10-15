# PlantPulse Central Server — DWSIM adapter contract

This central server is independent of the previous server/bridge. It listens only on
127.0.0.1:8770. Start it by double-clicking `start_central_server.bat`.

## Telemetry contract

A DWSIM-side adapter should POST JSON to one of these local endpoints every 1–5 seconds:

- `POST http://127.0.0.1:8770/api/telemetry/hx1`
- `POST http://127.0.0.1:8770/api/telemetry/pumptank`

Pump–tank payload should use explicit units and canonical keys, for example:

```json
{
  "process_id": "pumptank",
  "pump_flow_L_min": 10.0,
  "tank_level_m": 0.25,
  "tank_height_m": 2.0,
  "simulation_time_s": 0.0
}
```

The numbers above are examples, not actual values. The adapter must read the real objects
and properties from the user's DWSIM flowsheet. Do not fabricate live values.

HX1 payload should retain the dashboard's established schema when available:
`hot_in`, `hot_out`, `cold_in`, `cold_out` with `T_C`, `P_Pa`, and `W_kg_s`,
plus `duty_kW`. Other JSON telemetry is accepted and visible through the API.

## API

- `GET /api/health` — server health
- `GET /api/processes` — central process registry and connection state
- `GET /api/process/hx1/telemetry`
- `GET /api/process/pumptank/telemetry`
- `POST /api/telemetry/{hx1|pumptank}` — publish actual telemetry
- `POST /api/process/{hx1|pumptank}/setpoints` — queue local setpoints for an adapter

Setpoints are only queued in memory; they are **not** applied to DWSIM until a DWSIM-side
adapter explicitly reads them and writes the correct manipulated variable. Server state
resets when the process stops. This server is a local dashboard/API, not a safety system.

## Why the DWSIM adapter is still required

A standalone Python server cannot reliably inspect a running DWSIM flowsheet unless a
supported DWSIM automation interface or an in-process DWSIM script is connected. Object
names, property identifiers, and write/recalculation behavior differ by flowsheet. Once the
pump, tank, and stream object names are known, add an adapter to publish real telemetry.
This does not require locating or editing the old server file.
