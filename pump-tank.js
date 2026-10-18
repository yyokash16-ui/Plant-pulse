(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const endpoint = "/api/process/pumptank/telemetry";
  let timer = null;
  const fmt = (value, digits=2) => Number.isFinite(Number(value)) ? Number(value).toLocaleString(undefined,{maximumFractionDigits:digits,minimumFractionDigits:0}) : "—";
  const get = (obj, path) => path.split(".").reduce((v,k)=>v && Object.prototype.hasOwnProperty.call(v,k)?v[k]:undefined,obj);
  const metric = (id, value, unit="") => { const el=$(id); if(el) el.textContent = value === null || value === undefined || value === "" ? "—" : String(value) + (unit ? " " + unit : ""); };
  const value = (obj, path, digits=2, unit="") => {
    const n=get(obj,path);
    return Number.isFinite(Number(n)) && n !== null && n !== "" ? fmt(n,digits)+(unit ? " "+unit : "") : "—";
  };
  function status(text, kind="warn") {
    const el=$("ptStatus"); if(el){el.textContent=text;el.className="state "+kind;}
    const bridge=$("ptBridgeState"); if(bridge){bridge.textContent=text;bridge.className="state "+kind;}
  }
  function set(id, text){const el=$(id);if(el)el.textContent=text;}
  function render(data) {
    const t=data.telemetry||{};
    const connected=!!data.connected;
    status(connected ? "DWSIM DATA RECEIVED" : "WAITING FOR DWSIM", connected ? "good" : "warn");
    set("ptConnectionNote", connected
      ? "Central server received a DWSIM snapshot. Values below are from the steady-state flowsheet."
      : "No recent DWSIM snapshot. Open the central server and run your existing DWSIM telemetry script to send a fresh snapshot.");
    set("ptLastSeen", data.last_seen || "No snapshot received yet");
    set("ptAge", data.telemetry_age_s === null || data.telemetry_age_s === undefined ? "—" : fmt(data.telemetry_age_s,1)+" s ago");
    set("ptMode", t.simulation_mode || "Not supplied");
    set("ptSource", t.source || "Not supplied");
    set("ptFeedT", value(t,"feed.temperature_K",2,"K") + (Number.isFinite(Number(get(t,"feed.temperature_K"))) ? " ("+fmt(Number(get(t,"feed.temperature_K"))-273.15,2)+" °C)" : ""));
    set("ptFeedP", value(t,"feed.pressure_Pa",0,"Pa") + (Number.isFinite(Number(get(t,"feed.pressure_Pa"))) ? " ("+fmt(Number(get(t,"feed.pressure_Pa"))/100000,3)+" bar)" : ""));
    set("ptFeedMass", value(t,"feed.mass_flow_kg_s",4,"kg/s"));
    set("ptFeedVol", value(t,"feed.volumetric_flow_m3_s",6,"m³/s") + (Number.isFinite(Number(get(t,"feed.volumetric_flow_m3_s"))) ? " ("+fmt(Number(get(t,"feed.volumetric_flow_m3_s"))*60000,3)+" L/min)" : ""));
    set("ptOutT", value(t,"discharge.temperature_K",2,"K") + (Number.isFinite(Number(get(t,"discharge.temperature_K"))) ? " ("+fmt(Number(get(t,"discharge.temperature_K"))-273.15,2)+" °C)" : ""));
    set("ptOutP", value(t,"discharge.pressure_Pa",0,"Pa") + (Number.isFinite(Number(get(t,"discharge.pressure_Pa"))) ? " ("+fmt(Number(get(t,"discharge.pressure_Pa"))/100000,3)+" bar)" : ""));
    set("ptOutMass", value(t,"discharge.mass_flow_kg_s",4,"kg/s"));
    set("ptOutVol", value(t,"discharge.volumetric_flow_m3_s",6,"m³/s") + (Number.isFinite(Number(get(t,"discharge.volumetric_flow_m3_s"))) ? " ("+fmt(Number(get(t,"discharge.volumetric_flow_m3_s"))*60000,3)+" L/min)" : ""));
    set("ptPumpDP", value(t,"pump.pressure_increase_Pa",0,"Pa") + (Number.isFinite(Number(get(t,"pump.pressure_increase_Pa"))) ? " ("+fmt(Number(get(t,"pump.pressure_increase_Pa"))/100000,3)+" bar)" : ""));
    set("ptPumpEff", value(t,"pump.efficiency_percent",2,"%"));
    set("ptPumpHead", value(t,"pump.head_m",3,"m"));
    set("ptTankVolume", value(t,"tank.vessel_volume_m3",3,"m³"));
    set("ptResidence", value(t,"tank.residence_time_s",1,"s") + (Number.isFinite(Number(get(t,"tank.residence_time_s"))) ? " ("+fmt(Number(get(t,"tank.residence_time_s"))/60,2)+" min)" : ""));
    set("ptEnergy", value(t,"energy_stream.energy_flow_W",1,"W") + (Number.isFinite(Number(get(t,"energy_stream.energy_flow_W"))) ? " ("+fmt(Number(get(t,"energy_stream.energy_flow_W"))/1000,3)+" kW)" : ""));
    const raw=$("ptRaw");if(raw)raw.textContent=JSON.stringify(data,null,2);
    const missing=[];
    if(!t.feed)missing.push("feed stream");
    if(!t.discharge)missing.push("discharge stream");
    if(!t.pump)missing.push("pump");
    if(!t.tank)missing.push("tank");
    set("ptDataQuality",connected ? (missing.length ? "Snapshot received; missing: "+missing.join(", ")+ "." : "All configured pump–tank telemetry groups are present.") : "Disconnected or stale: values are not being refreshed.");
  }
  async function poll() {
    try {
      const response=await fetch(endpoint,{cache:"no-store"});
      const body=await response.json();
      if(!response.ok || !body.ok) throw new Error(body.error||("HTTP "+response.status));
      render(body);
    } catch(error) {
      status("SERVER UNAVAILABLE","bad");
      set("ptConnectionNote","Cannot read the PlantPulse central server. Confirm start_central_server.bat is running at http://127.0.0.1:8770.");
      set("ptLastSeen","Unavailable");
      set("ptAge","—");
      set("ptDataQuality","No server response: "+error.message);
      const raw=$("ptRaw");if(raw)raw.textContent="Connection error: "+error.message;
    }
  }
  const refresh=$("ptRefresh");if(refresh)refresh.addEventListener("click",poll);
  poll();
  timer=setInterval(poll,4000);
  window.addEventListener("pagehide",()=>{if(timer)clearInterval(timer);});
})();