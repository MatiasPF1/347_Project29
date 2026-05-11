// === NAV ===
document.getElementById('nav').addEventListener('click', e => {
  const b = e.target.closest('button[data-sec]');
  if (!b) return;
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById('sec-' + b.dataset.sec).classList.add('active');
  document.querySelectorAll('.nav button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
});

// === ENGINE (mirrors Av_Team29.py) ===
class SM { constructor(){this.logs=[];} log(m,a,d=''){const ts=new Date().toLocaleTimeString();const e={ts,mod:m,action:a,details:d};this.logs.push(e);return e;} }
class SF {
  constructor(s){this.s=s;this.ld=Infinity;this.ls=0;this.ttc=Infinity;this.obj=[];this.lo=0;this.sl=55;this.vd=false;}
  upd(d,l,o,off,lim){this.ld=d;this.ls=l;this.obj=o;this.lo=off;this.sl=lim;const c=Math.max(.1,this.ls);this.ttc=this.ld>0&&c>0?this.ld/c:Infinity;}
  ped(){return this.obj.find(o=>o.type==='pedestrian'||o.type==='cyclist')||null;}
}
class PL {
  constructor(f,s){this.f=f;this.s=s;}
  eval(){if(this.f.ttc<2)return this._c();const p=this.f.ped();if(p&&p.distance<15)return this._p(p);if(Math.abs(this.f.lo)>1)return this._l();return{action:'maintain'};}
  _c(){this.s.log('Planning','collision_threat',`ttc=${this.f.ttc.toFixed(2)}s`);return this.f.ttc<1?{action:'emergency_brake',force:1,details:`ttc=${this.f.ttc.toFixed(2)}s`}:{action:'brake',force:.6,details:`ttc=${this.f.ttc.toFixed(2)}s`};}
  _p(p){this.s.log('Planning','pedestrian_response',`${p.type} at ${p.distance}m`);return p.distance<5?{action:'full_stop',details:`${p.type} blocking`}:{action:'slow_down',speed:10,details:`${p.type} nearby`};}
  _l(){const o=this.f.lo,c=Math.min(20,Math.abs(o)*5),d=o<0?'right':'left';this.s.log('Planning','lane_correction',`offset=${o.toFixed(1)}ft, steer ${d}`);return{action:'steer',angle:c,direction:d};}
  traf(sig){const v=['RED','YELLOW','GREEN','STOP_SIGN'],cl=v.includes(sig)?sig:'RED';this.s.log('SensorFusion','signal_detected',cl);if(cl==='RED'||cl==='STOP_SIGN'){this.s.log('Planning','traffic_stop',cl);return{action:'full_stop',details:cl};}if(cl==='YELLOW'){this.s.log('Planning','traffic_decel','yellow');return{action:'decelerate',details:'yellow'};}this.s.log('Planning','traffic_proceed','green');return{action:'proceed',details:'green'};}
  fDist(spd,vis){let s=spd*2;if(vis)s*=1.5;this.s.log('Planning','following_distance',`safe=${s.toFixed(1)}m`);return s;}
}
class VC {
  constructor(s){this.s=s;this.spd=0;this.str=0;this.brk=0;}
  exec(cmd){const a=cmd.action;if(a==='emergency_brake'){this.brk=cmd.force||1;this.spd=0;}else if(a==='full_stop'){this.brk=1;this.spd=0;}else if(a==='brake'||a==='decelerate'){this.brk=cmd.force||.5;this.spd=Math.max(0,this.spd-this.brk*20);}else if(a==='slow_down'){this.spd=Math.min(this.spd,cmd.speed||10);}else if(a==='steer'){this.str=cmd.direction==='left'?-cmd.angle:cmd.angle;}else if(a==='proceed'){this.brk=0;}this.s.log('VCS',`execute_${a}`,`speed=${this.spd.toFixed(1)}, steer=${this.str.toFixed(1)}, brake=${this.brk.toFixed(1)}`);}
}

let sm, sf, pl, vc, von = false, ctrl = '—', logN = 0;
function init() { sm = new SM(); sf = new SF(sm); pl = new PL(sf, sm); vc = new VC(sm); }
init();

function aLog(e, t = 'sim-log') {
  const el = document.getElementById(t);
  const cls = e.action.includes('emergency') || e.action.includes('collision') || e.action.includes('locked') ? 'err' : e.action.includes('decel') ? 'warn' : '';
  const l = document.createElement('div'); l.className = `log-line ${cls}`;
  l.innerHTML = `<span class="ts">${e.ts}</span> <span class="mod">${e.mod}</span> <span class="act">${e.action}</span> <span class="det">${e.details}</span>`;
  el.appendChild(l); el.scrollTop = el.scrollHeight; logN++;
  const lc = document.getElementById('log-count'); if (lc) lc.textContent = logN + ' events';
}
function uDash() {
  document.getElementById('v-speed').textContent = vc.spd.toFixed(0);
  document.getElementById('v-controller').textContent = ctrl;
  document.getElementById('v-status').textContent = von ? 'ON' : 'OFF';
  document.getElementById('v-ttc').textContent = sf.ttc === Infinity ? '∞' : sf.ttc.toFixed(2);
  document.getElementById('v-brake').textContent = vc.brk.toFixed(1);
  document.getElementById('v-steer').textContent = vc.str.toFixed(1) + '°';
  document.getElementById('d-speed').className = 'dash-item ' + (vc.spd === 0 ? '' : vc.spd > 80 ? 'warn' : 'ok');
  document.getElementById('d-ttc').className = 'dash-item ' + (sf.ttc < 1 ? 'alert' : sf.ttc < 3 ? 'warn' : sf.ttc === Infinity ? '' : 'ok');
  document.getElementById('d-brake').className = 'dash-item ' + (vc.brk > .8 ? 'alert' : vc.brk > 0 ? 'warn' : '');
  document.getElementById('d-status').className = 'dash-item ' + (von ? 'ok' : '');
  // HUD overlay
  const hudSpd = document.getElementById('hud-spd');
  const hudMode = document.getElementById('hud-mode');
  if (hudSpd) hudSpd.textContent = vc.spd.toFixed(0) + ' km/h';
  if (hudMode) hudMode.textContent = von ? ctrl : 'OFF';
  // road scroll & car bob
  setCarMoving(von && vc.spd > 0 && vc.brk < 1);
}
function setTL(c) { document.getElementById('tl-r').classList.toggle('on', c === 'RED'); document.getElementById('tl-y').classList.toggle('on', c === 'YELLOW'); document.getElementById('tl-g').classList.toggle('on', c === 'GREEN'); }
function setD(d) { const c = document.getElementById('car-icon'); c.classList.remove('drift-left', 'drift-right'); if (d) c.classList.add('drift-' + d); }
function setO(i, v) { const e = document.getElementById('obstacle-icon'); e.textContent = i; e.classList.toggle('visible', v); }
function setR(a) { document.getElementById('detect-ring').classList.toggle('active', a); }
function setCarMoving(moving) {
  const dashes = document.getElementById('road-dashes');
  const car = document.getElementById('car-icon');
  if (!dashes || !car) return;
  if (moving) {
    dashes.classList.add('moving');
    car.style.animation = 'car-bob 0.35s ease-in-out infinite';
  } else {
    dashes.classList.remove('moving');
    car.style.animation = '';
  }
}
function clrV() { setTL(''); setD(''); setO('', false); setR(false); setCarMoving(false); }

function runScenario(n) {
  clrV(); const s = [];
  if (n === 'startup') { von = true; ctrl = 'Auto'; s.push(() => aLog(sm.log('Vehicle', 'started', 'card tap verified'))); s.push(() => aLog(sm.log('Vehicle', 'system_checks', 'all sensors online'))); s.push(() => { vc.spd = 0; uDash(); }); }
  else if (n === 'cruise') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 50; s.push(() => aLog(sm.log('Vehicle', 'cruise_on', '50 km/h'))); s.push(() => aLog(sm.log('Vehicle', 'adaptive_cruise_on', 'following at 30m'))); s.push(() => { sf.vd = true; aLog(sm.log('SensorFusion', 'visibility_degraded', 'low visibility')); }); s.push(() => { pl.fDist(50, true); aLog(sm.logs[sm.logs.length - 1]); uDash(); }); }
  else if (n === 'emergency') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 45; s.push(() => { sf.upd(3, 15, [], 0, 55); aLog(sm.log('SensorFusion', 'sync', 'LiDAR+Camera+RADAR')); }); s.push(() => { aLog(sm.log('SensorFusion', 'ttc_computed', `ttc=${sf.ttc.toFixed(2)}s`)); setR(true); setO('🚙', true); }); s.push(() => { pl.eval(); aLog(sm.logs[sm.logs.length - 1]); aLog(sm.log('Planning', 'emergency_brake', 'force=1.0')); }); s.push(() => { vc.exec({ action: 'emergency_brake', force: 1 }); aLog(sm.logs[sm.logs.length - 1]); uDash(); }); }
  else if (n === 'pedestrian') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 25; s.push(() => { sf.upd(50, 0, [{ type: 'pedestrian', distance: 3 }], 0, 30); setO('🚶', true); setR(true); }); s.push(() => aLog(sm.log('SensorFusion', 'pedestrian_detected', 'pedestrian at 3m'))); s.push(() => { pl.eval(); aLog(sm.logs[sm.logs.length - 1]); }); s.push(() => { vc.exec({ action: 'full_stop', details: 'pedestrian blocking' }); aLog(sm.logs[sm.logs.length - 1]); uDash(); }); }
  else if (n === 'lane_drift') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 55; s.push(() => { sf.lo = -1.5; setD('left'); aLog(sm.log('Vehicle', 'lane_monitor', 'offset=-1.5ft')); }); s.push(() => { pl._l(); aLog(sm.logs[sm.logs.length - 1]); }); s.push(() => { vc.exec({ action: 'steer', angle: 7.5, direction: 'right' }); aLog(sm.logs[sm.logs.length - 1]); setD(''); }); s.push(() => { sf.lo = 0; uDash(); aLog(sm.log('Vehicle', 'lane_centered', 'corrected')); }); }
  else if (n === 'traffic_red') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 35; s.push(() => setTL('RED')); s.push(() => { pl.traf('RED'); aLog(sm.logs[sm.logs.length - 2]); aLog(sm.logs[sm.logs.length - 1]); }); s.push(() => { vc.exec({ action: 'full_stop', details: 'RED' }); aLog(sm.logs[sm.logs.length - 1]); uDash(); }); }
  else if (n === 'traffic_green') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 35; s.push(() => setTL('GREEN')); s.push(() => { pl.traf('GREEN'); aLog(sm.logs[sm.logs.length - 2]); aLog(sm.logs[sm.logs.length - 1]); }); s.push(() => { vc.brk = 0; uDash(); }); }
  else if (n === 'override') { if (!von) { alert('Start the vehicle first.'); return; } s.push(() => { aLog(sm.log('Vehicle', 'control_transfer', 'Auto → Human')); ctrl = 'Human'; }); s.push(() => { aLog(sm.log('Planning', 'suspended', 'autonomous paused')); uDash(); }); s.push(() => { aLog(sm.log('Vehicle', 'control_transfer', 'Human → Auto')); ctrl = 'Auto'; uDash(); }); }
  else if (n === 'crash_detect') { if (!von) { alert('Start the vehicle first.'); return; } vc.spd = 40; s.push(() => { sf.upd(10, 5, [], 0, 55); setR(true); setO('🚙', true); }); s.push(() => aLog(sm.log('SensorFusion', 'ttc_computed', `ttc=${sf.ttc.toFixed(2)}s`))); s.push(() => { pl.eval(); aLog(sm.logs[sm.logs.length - 1]); }); s.push(() => { vc.exec({ action: 'brake', force: .6 }); aLog(sm.logs[sm.logs.length - 1]); uDash(); }); }
  s.forEach((fn, i) => setTimeout(fn, i * 450));
  setTimeout(uDash, s.length * 450 + 100);
}
function clearSim() { init(); von = false; ctrl = '—'; logN = 0; document.getElementById('sim-log').innerHTML = '<div class="log-line"><span class="ts">ready</span> <span class="det">Reset. Click a scenario to begin.</span></div>'; document.getElementById('log-count').textContent = '0 events'; clrV(); uDash(); }

// === TECHNICIAN ===
let tA = 0, tIn = false;
function tLog(m, a, d) { const el = document.getElementById('tech-log'), l = document.createElement('div'); l.className = `log-line ${a.includes('failed') || a.includes('locked') ? 'err' : ''}`; l.innerHTML = `<span class="ts">${new Date().toLocaleTimeString()}</span> <span class="mod">${m}</span> <span class="act">${a}</span> <span class="det">${d}</span>`; el.appendChild(l); el.scrollTop = el.scrollHeight; }
function techLogin() {
  const u = document.getElementById('tech-user').value, p = document.getElementById('tech-pass').value, o = document.getElementById('tech-otp').value;
  if (tA >= 3) { document.getElementById('tech-status').innerHTML = '<span class="badge red">locked</span> Too many attempts.'; tLog('SystemMgmt', 'account_locked', u); return; }
  if (u === 'tech1' && p === 'securepass123' && o === '123456') { tIn = true; tA = 0; document.getElementById('tech-status').innerHTML = `<span class="badge green">authenticated</span> Welcome, ${u}`; document.getElementById('tech-panel').style.opacity = '1'; document.getElementById('tech-panel').style.pointerEvents = 'auto'; tLog('SystemMgmt', 'technician_login', `${u} logged in (MFA)`); }
  else { tA++; document.getElementById('tech-status').innerHTML = `<span class="badge red">failed</span> Attempt ${tA}/3`; tLog('SystemMgmt', 'login_failed', `${u} attempt ${tA}`); if (tA >= 3) { document.getElementById('tech-status').innerHTML += ' <span class="badge red">locked</span>'; tLog('SystemMgmt', 'account_locked', u); } }
}
function techLogout() { tIn = false; document.getElementById('tech-status').innerHTML = '<span class="badge yellow">logged out</span>'; document.getElementById('tech-panel').style.opacity = '0.35'; document.getElementById('tech-panel').style.pointerEvents = 'none'; tLog('SystemMgmt', 'technician_logout', 'session ended'); }
function techViewLogs() { if (!tIn) return; tLog('SystemMgmt', 'view_logs', `${sm.logs.length} entries`); document.getElementById('tech-result').innerHTML = '<div style="font-size:.78rem;color:var(--green)">✅ Logs retrieved.</div>'; }
function techRunDiag() {
  if (!tIn) return;
  tLog('SystemMgmt', 'diagnostics', 'running');
  const r = document.getElementById('tech-result');
  r.innerHTML = '<div style="font-size:.78rem;color:var(--yellow)">Running...</div>';
  setTimeout(() => { r.innerHTML = '<div style="font-size:.78rem;color:var(--green)">✅ All modules OK</div><div style="font-size:.68rem;color:var(--text2);margin-top:4px;font-family:\'IBM Plex Mono\',monospace">SensorFusion · Planning · VCS · SystemMgmt — all operational</div>'; tLog('SystemMgmt', 'diagnostics_complete', 'all OK'); }, 1200);
}
function techUpdate() {
  if (!tIn) return;
  tLog('SystemMgmt', 'ota_update', 'installing v2.1.0');
  const r = document.getElementById('tech-result');
  r.innerHTML = '<div style="font-size:.78rem;color:var(--yellow)">Downloading...</div>';
  setTimeout(() => r.innerHTML = '<div style="font-size:.78rem;color:var(--yellow)">Installing...</div>', 800);
  setTimeout(() => { r.innerHTML = '<div style="font-size:.78rem;color:var(--green)">✅ v2.1.0 installed</div>'; tLog('SystemMgmt', 'ota_update', 'v2.1.0 installed'); }, 2000);
}

uDash();
