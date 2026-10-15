# DWSIM pump–tank integration contract

## Physical model

Configuration target: one pump fills a vertical cylindrical tank; the outlet is closed; no liquid leaves the tank.

For constant liquid density and a vertical cylinder with constant cross-sectional area:

- (A = pi D^2/4)
- (dV/dt = Q_{in}), because (Q_{out}=0)
- (A,dh/dt = Q_{in}), therefore (dh/dt=Q_{in}/A)
- For constant flow, (h(t)=\min(H, h_0+Q_{in}t/A))

Convert flow to SI before calculation: (Q_{m^3/s}=Q_{L/min}/60000). Clamp level to ([0,H]). The model assumes an incompressible liquid, constant tank area, no leakage, and no overflow model. When the tank reaches (H), filling should stop or raise a high-level condition in the DWSIM model.

## DWSIM flowsheet setup

1. Use a liquid feed, pump, and DWSIM Tank unit operation connected in sequence.
2. Configure the tank's total volume as (V=\pi D^2H/4) and set its dynamic height to (H). Example dashboard defaults are (D=0.8\,m), (H=2.0\,m), and (h_0=0.25\,m); replace them with the actual apparatus dimensions.
3. Activate Dynamic Mode. Configure the inlet stream's dynamic specification to flow where appropriate, and ensure the pump and tank are supported in Dynamic Mode.
4. Keep the tank outlet closed for this scenario. If the flowsheet requires an outlet path, use a valve that remains fully closed during the filling test and verify the calculated outlet flow is zero.
5. Initialize the tank's contents/level, store a known initial flowsheet state, create a Dynamics Manager integrator and schedule, and monitor tank Liquid Level, inlet flow, and simulation time. Run a short test and confirm level rises with flow and does not exceed the configured height.
6. Validate the DWSIM result against the mass-balance estimate using the actual geometry, units, and inlet volumetric flow. If DWSIM reports mass flow, convert using the liquid density: (Q=\dot m/\rho).

DWSIM menu labels and dynamic-property panels may differ by version. Do not use the dashboard defaults as real equipment data.

## Local bridge contract expected by PlantPulse

The existing local bridge at `127.0.0.1:8765` was previously built for HX1. PlantPulse now proxies an optional `GET /api/pumptank` endpoint first and falls back to the existing `GET /api/hx1` endpoint for connection diagnostics. The existing HX1 bridge does **not** automatically become a pump–tank bridge.

To show actual DWSIM pump/tank telemetry, extend the local bridge to return a JSON object with explicitly named SI/declared-unit fields, for example:

```json
{
  "pump_flow_L_min": 10.0,
  "tank_level_m": 0.25,
  "simulation_time_s": 0.0,
  "tank_diameter_m": 0.8,
  "tank_height_m": 2.0
}
```

PlantPulse recognizes `pump_flow_L_min`, `tank_level_m`, and `simulation_time_s` (also camel-case equivalents documented in `pump-tank.js`). The app deliberately ignores generic fields like `flow` because their units and meaning are ambiguous.

- If `pump_flow_L_min` is present, the dynamic estimator uses that reported pump flow as its input.
- If `tank_level_m` is present, PlantPulse displays it as bridge telemetry, separately from the model-estimated level.
- If those tags are absent, the local dashboard estimator uses the entered flow and labels the calculated level as a **model estimate**, not a DWSIM result.
- No write/control endpoint is implemented for pump setpoints. The existing `/api/hx1/set` route is HX1-specific and must not be assumed to accept pump commands.

The bridge must read the currently loaded DWSIM flowsheet's actual objects/properties and actual dynamic simulation time. Do not return hard-coded values or mirror the dashboard estimator and call them DWSIM telemetry. Keep the server loopback-only.
