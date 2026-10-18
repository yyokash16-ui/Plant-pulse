# PlantPulse continuous DWSIM connector (IronPython / DWSIM Script Manager)
# Open Tank system.dwxmz first, then run this script once in Script Manager.
# It publishes read-only steady-state snapshots every 2 seconds to localhost:8770.
# It does not change process variables or control the simulation.

import json
import time
import clr
clr.AddReference("System")
clr.AddReference("System.Net")
from System.Timers import Timer
from System.Net import WebClient

URL = "http://127.0.0.1:8770/api/telemetry/pumptank"
INTERVAL_MS = 2000

def _obj(tag):
    # Confirmed object tags in the user's Tank system.dwxmz flowsheet.
    return Flowsheet.SimulationObjects[tag]

def _call(obj, method):
    try:
        return float(getattr(obj, method)())
    except:
        return None

def _prop(obj, names):
    for name in names:
        try:
            value = getattr(obj, name)
            if callable(value):
                value = value()
            if value is not None:
                return float(value)
        except:
            pass
    return None

def _safe_div(a, b):
    try:
        if a is not None and b not in (None, 0):
            return float(a) / float(b)
    except:
        pass
    return None

def _snapshot():
    feed = _obj("PUMP")
    discharge = _obj("2")
    pump = _obj("PUMP-1")
    tank = _obj("TANK-1")
    energy = _obj("E1")

    ft = _call(feed, "GetTemperature")
    fp = _call(feed, "GetPressure")
    fm = _call(feed, "GetMassFlow")
    fv = _call(feed, "GetVolumetricFlow")

    dt = _call(discharge, "GetTemperature")
    dp = _call(discharge, "GetPressure")
    dm = _call(discharge, "GetMassFlow")
    dv = _call(discharge, "GetVolumetricFlow")

    pressure_rise = None if fp is None or dp is None else dp - fp
    density = _safe_div(fm, fv)
    head = None if pressure_rise is None or not density else pressure_rise / (density * 9.80665)
    vessel_volume = _prop(tank, ["Volume", "VesselVolume", "Volume_m3"])
    residence = _safe_div(vessel_volume, fv)

    efficiency = _prop(pump, ["Efficiency", "PumpEfficiency"])
    if efficiency is not None and efficiency <= 1.0:
        efficiency = efficiency * 100.0
    energy_flow = _call(energy, "GetEnergyFlow")
    if energy_flow is None:
        energy_flow = _prop(energy, ["EnergyFlow", "EnergyFlow_W", "Power"])

    return {
        "source": "DWSIM Script Manager continuous connector",
        "simulation_mode": "steady-state",
        "sent_at_unix": time.time(),
        "feed": {
            "temperature_K": ft, "pressure_Pa": fp,
            "mass_flow_kg_s": fm, "volumetric_flow_m3_s": fv
        },
        "discharge": {
            "temperature_K": dt, "pressure_Pa": dp,
            "mass_flow_kg_s": dm, "volumetric_flow_m3_s": dv
        },
        "pump": {
            "pressure_increase_Pa": pressure_rise,
            "efficiency_percent": efficiency,
            "head_m": head
        },
        "tank": {
            "vessel_volume_m3": vessel_volume,
            "residence_time_s": residence
        },
        "energy_stream": {"energy_flow_W": energy_flow}
    }

def _publish(sender=None, args=None):
    try:
        payload = _snapshot()
        client = WebClient()
        try:
            client.Headers["Content-Type"] = "application/json"
            response = client.UploadString(URL, "POST", json.dumps(payload))
            print("PlantPulse: DWSIM snapshot sent successfully.")
        finally:
            client.Dispose()
    except Exception as exc:
        print("PlantPulse connector error: " + str(exc))

# Stop a previous copy if this script is run again.
try:
    _plantpulse_timer.Stop()
    _plantpulse_timer.Dispose()
except:
    pass

# Send the first snapshot immediately, then refresh every 2 seconds.
_publish()
_plantpulse_timer = Timer(INTERVAL_MS)
_plantpulse_timer.AutoReset = True
_plantpulse_timer.Elapsed += _publish
_plantpulse_timer.Start()
print("PlantPulse connector running: publishing DWSIM telemetry every 2 seconds.")
print("Keep DWSIM and PlantPulse-Central.exe open. Run this script only once per session.")
