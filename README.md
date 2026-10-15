# PlantPulse — DWSIM Digital Twin

PlantPulse is a responsive local dashboard for DWSIM simulation telemetry. It retains the HX1 heat-exchanger page and adds a pump–tank dynamic filling estimator for a vertical cylindrical tank with a closed outlet. The pump–tank page can consume explicitly named telemetry from an extended local bridge; the existing HX1 bridge alone does not provide pump–tank integration.

## Start on Windows

1. Install Python 3.10 or newer.
2. Open DWSIM and load the intended simulation.
3. Start your existing HX1 bridge. Default endpoints:
   - `GET http://127.0.0.1:8765/api/status`
   - `GET http://127.0.0.1:8765/api/hx1`
   - `POST http://127.0.0.1:8765/api/hx1/set`
4. Double-click `start_plantpulse.bat`.
5. Open `http://127.0.0.1:8766` in Edge or Chrome.

PlantPulse's Python server proxies the bridge API on the same local origin. It binds to `127.0.0.1` only and does not expose the dashboard to your LAN.

## Features

- HX1 hot/cold inlet and outlet temperatures.
- Heat duty, pressure and mass flow when present in the bridge response.
- Raw JSON viewer and numeric variable table for debugging.
- Connection diagnostics and CSV export of local-session values.
- Optional HX1 write-through to `/api/hx1/set`, disabled by default and guarded by a confirmation dialog. This is not a pump setpoint endpoint.
- Pump–tank page with tank geometry inputs, dynamic filling estimate, level trend, volume, fill percentage, and estimated time to full.
- Optional canonical pump–tank telemetry via a future/extended `GET /api/pumptank` bridge endpoint.

## Expected telemetry

The dashboard recognizes the previous HX1 schema: `hot_in`, `hot_out`, `cold_in`, `cold_out` objects with `T_C`, `P_Pa`, and `W_kg_s`, plus `duty_kW`. If your bridge returns different fields, raw JSON and detected numeric values are still displayed. Verify actual fields and units against the running bridge.

## Pump–tank dynamic model\n\nThe filling estimator uses `A dh/dt = Qin` for a vertical cylinder with a closed outlet (`Qout = 0`), where `A = pi D^2 / 4`. The dashboard converts L/min to m³/s, integrates the transient, and clamps the estimated level at the configured tank height. Unless the local DWSIM bridge exposes canonical pump/tank tags, these are local model estimates and not results from the DWSIM dynamic solver. See [the DWSIM pump–tank integration guide](docs/PUMP_TANK_DWSIM_BRIDGE.md) for flowsheet setup and the bridge JSON contract.\n\n## Writing values

The controls page requires enabling writes, entering a JSON object and confirming every request. Prior bridge iterations used temperature fields such as `hot_in_C` and `cold_in_C`; check your installed bridge code before using those names. This application is for DWSIM simulation interaction, not live plant control.

## Get the Windows app\n\nA Windows executable is built automatically by GitHub Actions after changes to `main`. Open the repository **Actions** tab, select **Build PlantPulse Windows App**, open the latest successful run, and download the `PlantPulse-Windows` artifact. Extract it and run `PlantPulse.exe`. Keep DWSIM and your existing HX1 bridge running.\n\n## Limitations and safety

- Your existing bridge must be running and attached to the intended DWSIM flowsheet.
- If a write reaches the bridge but DWSIM does not update, inspect bridge object bindings and recalculation logic.
- GitHub Pages cannot run Python or connect to a process on your PC. Use the local URL above for DWSIM connectivity.
- Simulation data is not plant instrumentation. Do not use this for safety-critical decisions or expose control endpoints publicly.

## Troubleshooting

- Confirm `http://127.0.0.1:8765/api/status` opens while DWSIM and the HX1 bridge are running.
- If port 8766 is occupied, close the other process or set `PLANTPULSE_PORT`.
- To change the bridge port, set `DWSIM_BRIDGE_URL` before launching `server.py`.
