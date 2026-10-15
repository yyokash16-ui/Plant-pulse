(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const cfg = { diameter: 0.8, height: 2.0, initial: 0.25, flow: 10 };
  let level = cfg.initial, elapsed = 0, running = false, lastTick = null, timer = null;
  let history = [], dwsim = { connected: false, flow: null, level: null, time: null, payload: null };
  const area = () => Math.PI * Math.pow(Number($("ptDiameter").value), 2) / 4;
  const tankHeight = () => Number($("ptHeight").value);
  const flow = () => Math.max(0, dwsim && dwsim.connected && dwsim.flow !== null ? dwsim.flow : (Number($("ptFlow").value) || 0));
  const valid = () => Number($("ptDiameter").value) > 0 && tankHeight() > 0 &&
    Number($("ptInitial").value) >= 0 && Number($("ptInitial").value) <= tankHeight() && flow() >= 0;
  const fmt = (n, d=3) => Number.isFinite(n) ? n.toFixed(d) : "—";
  function setStatus(text, kind="warn") { const e=$("ptStatus"); e.textContent=text; e.className="state "+kind; }
  function notice(text) { $("ptMessage").textContent=text; }
  function pushPoint() {
    history.push({ t: elapsed, h: level, q: flow() });
    if (history.length > 900) history.shift();
  }
  function renderChart() {
    const c=$("ptChart"); if(!c) return;
    const w=Math.max(320,c.clientWidth||600), h=210, dpr=window.devicePixelRatio||1;
    c.width=w*dpr; c.height=h*dpr; c.style.height=h+"px";
    const ctx=c.getContext("2d"); ctx.scale(dpr,dpr); ctx.clearRect(0,0,w,h);
    const pad={l:42,r:12,t:14,b:30}, pw=w-pad.l-pad.r, ph=h-pad.t-pad.b;
    ctx.strokeStyle="#293d48"; ctx.lineWidth=1; ctx.fillStyle="#91a4b1"; ctx.font="10px system-ui";
    for(let i=0;i<=4;i++){let y=pad.t+ph*i/4;ctx.beginPath();ctx.moveTo(pad.l,y);ctx.lineTo(w-pad.r,y);ctx.stroke();ctx.fillText(fmt(tankHeight()*(1-i/4),2),3,y+3);}
    if(history.length<2){ctx.fillText("Start the fill simulation to plot level history.",pad.l+8,pad.t+ph/2);return;}
    const t0=history[0].t,t1=Math.max(t0+1,history[history.length-1].t);
    ctx.strokeStyle="#55d6a3";ctx.lineWidth=2;ctx.beginPath();
    history.forEach((p,i)=>{const x=pad.l+(p.t-t0)/(t1-t0)*pw,y=pad.t+ph-(Math.max(0,Math.min(tankHeight(),p.h))/tankHeight())*ph;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();
    ctx.fillText("Elapsed simulation time (s)",Math.max(pad.l,w/2-60),h-7);
  }
  function render() {
    if(!valid()){setStatus("CHECK INPUTS","bad");return}
    const A=area(), H=tankHeight(), Q=flow()/60000, capacity=A*H, volume=A*level;
    const pct=H>0?100*level/H:0, rate=Q/A;
    $("ptLevel").textContent=fmt(level,3)+" m";
    $("ptPercent").textContent=fmt(pct,1)+"%";
    $("ptVolume").textContent=fmt(volume*1000,2)+" L";
    $("ptRate").textContent=fmt(rate*60,4)+" m/min";
    $("ptElapsed").textContent=fmt(elapsed,1)+" s";
    $("ptFill").style.width=Math.max(0,Math.min(100,pct))+"%";
    $("ptTankWater").style.height=Math.max(0,Math.min(100,pct))+"%";
    $("ptTankWater").style.bottom="0";
    $("ptTankMark").textContent=fmt(level,3)+" m / "+fmt(H,2)+" m";
    const remain=Math.max(0,H-level);
    $("ptTimeFull").textContent=Q>0&&level<H?fmt(remain*A/Q,1)+" s":level>=H?"FULL": "∞ (pump flow is zero)";
    $("ptEq").textContent="dh/dt = Qᵢₙ / A = "+fmt(Q,7)+" / "+fmt(A,5)+" = "+fmt(rate,7)+" m/s";
    $("ptModelInfo").textContent="Vertical cylinder · closed outlet · no outflow · incompressible liquid · constant cross-sectional area";
    $("ptFlowSource").textContent=dwsim.connected && dwsim.flow!==null ? "DWSIM bridge tag detected" : "Manual setpoint · local dynamic estimator";
    $("ptDwsimFlow").textContent=dwsim.flow===null?"Not available":fmt(dwsim.flow,3)+" L/min";
    $("ptDwsimLevel").textContent=dwsim.level===null?"Not available":fmt(dwsim.level,3)+" m";
    $("ptDwsimTime").textContent=dwsim.time===null?"Not available":fmt(dwsim.time,2)+" s";
    renderChart();
  }
  function tick(now) {
    if(!running) return;
    if(lastTick===null) lastTick=now;
    const dt=Math.min(1.0,Math.max(0,(now-lastTick)/1000)); lastTick=now;
    if(!valid()){pause();return}
    const H=tankHeight(), Q=flow()/60000, A=area();
    // Dynamic material balance for a vertical cylinder, with the outlet closed:
    // A dh/dt = Qin; integrate the measured wall-clock step and clamp at tank capacity.
    if(level < H && Q > 0) { level=Math.min(H,level+(Q/A)*dt); elapsed+=dt; pushPoint(); }
    if(level>=H){level=H;running=false;lastTick=null;setStatus("TANK FULL","bad");$("ptStart").textContent="▶ Start filling";notice("Tank reached its configured maximum level. Pump filling is paused by the estimator.");}
    else setStatus("DYNAMIC MODEL RUNNING","good");
    render();
  }
  function start() {
    if(!valid()){notice("Check tank diameter, height, initial level and pump flow.");return}
    if(level>=tankHeight()){notice("Tank is full. Reset or lower the initial level before filling again.");return}
    running=true;lastTick=null;setStatus("DYNAMIC MODEL RUNNING","good");
    $("ptStart").textContent="Ⅱ Pause";notice("Local dynamic estimator is integrating the tank mass balance. This is not yet a DWSIM solver result.");
    if(!timer)timer=setInterval(()=>tick(performance.now()),250);
  }
  function pause(){running=false;lastTick=null;$("ptStart").textContent="▶ Start filling";if(timer){clearInterval(timer);timer=null}setStatus("PAUSED","warn");render()}
  function reset(){
    pause(); level=Number($("ptInitial").value)||0;elapsed=0;history=[];pushPoint();
    setStatus("RESET","warn");notice("Level reset to the configured initial condition. Start filling to run the transient.");render();
  }
  function updateInputs(){
    if(!valid()){setStatus("CHECK INPUTS","bad");notice("Diameter and height must be positive; initial level must be between zero and tank height.");return}
    if(!running && history.length===0){level=Number($("ptInitial").value);pushPoint()}
    // Editing the initial level only changes the state when reset is pressed.
    $("ptInitialHelp").textContent="Current state: "+fmt(level,3)+" m. Press Reset to apply a new initial level.";
    render();
  }
  function findCanonical(obj, keys) {
    if(!obj||typeof obj!=="object")return null;
    for(const k of keys) if(Object.prototype.hasOwnProperty.call(obj,k) && Number.isFinite(Number(obj[k]))) return Number(obj[k]);
    for(const v of Object.values(obj)){const found=findCanonical(v,keys);if(found!==null)return found}
    return null;
  }
  async function pollBridge(){
    try {
      let r=await fetch("/api/bridge/pumptank",{cache:"no-store"}); let body=await r.json();
      if(!r.ok){r=await fetch("/api/bridge/hx1",{cache:"no-store"});body=await r.json();}
      if(!r.ok)throw new Error(body.error||("HTTP "+r.status));
      dwsim.connected=true;dwsim.payload=body;
      // Only use explicitly named canonical pump/tank fields; never guess units from generic "flow" keys.
      dwsim.flow=findCanonical(body,["pump_flow_L_min","pumpFlowLMin","pump_flow_l_min"]);
      dwsim.level=findCanonical(body,["tank_level_m","tankLevelM"]);
      dwsim.time=findCanonical(body,["simulation_time_s","simulationTimeS"]);
      if(dwsim.flow!==null) $("ptFlow").value=String(dwsim.flow);
      $("ptBridgeState").textContent="BRIDGE RESPONDS";$("ptBridgeState").className="state good";
      $("ptBridgeMessage").textContent=(dwsim.flow!==null||dwsim.level!==null)?"Canonical pump/tank tag(s) detected in the HX1 bridge response.":"The bridge responds, but no canonical pump/tank tags were found. Entered pump flow drives the local level estimate.";
      $("ptRaw").textContent=JSON.stringify(body,null,2);
    } catch(e) {
      dwsim.connected=false;dwsim.flow=null;dwsim.level=null;dwsim.time=null;
      $("ptBridgeState").textContent="NOT CONNECTED";$("ptBridgeState").className="state warn";
      $("ptBridgeMessage").textContent="No response from the pump/tank or HX1 bridge endpoints. Start PlantPulse and the local bridge at 127.0.0.1:8765. The local model can still be explored independently.";
      $("ptRaw").textContent="No bridge response: "+e.message;
    }
    render();
  }
  $("ptStart").addEventListener("click",()=>running?pause():start());
  $("ptReset").addEventListener("click",reset);
  ["ptDiameter","ptHeight","ptInitial","ptFlow"].forEach(id=>$(id).addEventListener("input",updateInputs));
  $("ptFlow").addEventListener("change",()=>{if(running)notice("Pump flow setpoint changed. The new rate is applied from the next integration step.");});
  $("ptRefresh").addEventListener("click",pollBridge);
  pushPoint();render();pollBridge();setInterval(pollBridge,4000);
  window.addEventListener("resize",renderChart);
})();