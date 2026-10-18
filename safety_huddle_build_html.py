#!/usr/bin/env python3
"""Build a single self-contained HTML version of the Safety Huddle Generator
that runs in a browser on a Windows work laptop (no Python, no Chrome headless)."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import safety_huddle  # noqa: E402  (reuses TOPICS + CSS verbatim)

def _logo_file():
    """Canonical brand path on this machine first, else a repo-local copy."""
    for p in (safety_huddle.LOGO_B64_FILE, os.path.join(HERE, "brand", "logo-print-b64.txt")):
        if os.path.exists(p):
            return p
    raise SystemExit("logo not found - expected " + safety_huddle.LOGO_B64_FILE)

TOPICS_JSON = json.dumps(safety_huddle.TOPICS)
LOGO = open(_logo_file()).read().strip()
CSS = safety_huddle.CSS

JS = r"""
const TOPICS = __TOPICS_JSON__;
const LOGO = "__LOGO__";
const TOPIC_BY_ID = {};
TOPICS.forEach(t => { TOPIC_BY_ID[t.id] = t; });
const MONTHS = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];
const MONTHS_ES = ["enero","febrero","marzo","abril","mayo","junio",
                "julio","agosto","septiembre","octubre","noviembre","diciembre"];
const DAYS_ES = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"];
let LANG = (new URLSearchParams(location.search).get("lang") === "es" || localStorage.getItem("sh_lang") === "es") ? "es" : "en";
function lg(t, key) { const es = "es_" + key; return (LANG === "es" && t[es] !== undefined) ? t[es] : t[key]; }

function isoWeek(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d - yStart) / 86400000) + 1) / 7);
}
function mondayOfWeek(weekNum, year) {
  const jan4 = new Date(year, 0, 4);
  const pyDow = (jan4.getDay() + 6) % 7;           // Python weekday(): Mon=0
  const startW1 = new Date(jan4); startW1.setDate(jan4.getDate() - pyDow);
  const mon = new Date(startW1); mon.setDate(startW1.getDate() + (weekNum - 1) * 7);
  return mon;
}
function pad(n) { return n < 10 ? "0" + n : "" + n; }
function fmtMD(d)  { return (LANG === "es" ? MONTHS_ES[d.getMonth()] : MONTHS[d.getMonth()]) + " " + pad(d.getDate()); }
function fmtMDY(d) { return fmtMD(d) + (LANG === "es" ? "" : ", " + d.getFullYear()); }

function selectTopics(weekNum) {
  const n = TOPICS.length;
  const start = (weekNum * 3) % n;
  const idx = [];
  for (let i = 0; i < 6; i++) idx.push((start + i) % n);
  return {
    left:   [TOPICS[idx[0]], TOPICS[idx[1]], TOPICS[idx[2]]],
    right:  [TOPICS[idx[3]], TOPICS[idx[4]], TOPICS[idx[5]]],
    bottom: ["cameras", "phones", "three_points"].map(b => TOPIC_BY_ID[b]),
  };
}

function renderSection(t) {
  const c = t.color || "s-blue", ic = t.icon || "&#9679;", ttl = lg(t, "title");
  const lines = ['<div class="section ' + c + '">',
    '  <div class="section-header">' + ic + " " + ttl + "</div>",
    '  <div class="section-body">'];
  if (t.checklist) {
    lines.push('    <ul class="checklist">');
    t.checklist.forEach(i => lines.push("      <li>" + i + "</li>"));
    lines.push("    </ul>");
  } else if (t.items) {
    lines.push("    <ul>");
    lg(t, "items").forEach(i => lines.push("      <li>" + i + "</li>"));
    lines.push("    </ul>");
  }
  if (t.stat_cards) {
    lines.push('    <div class="stat-row">');
    t.stat_cards.forEach(sc => lines.push(
      '      <div class="stat-card"><div class="num">' + sc[0] + '</div><div class="label">' + sc[1] + "</div></div>"));
    lines.push("    </div>");
  }
  if (t.columns) {
    lines.push('    <div class="two-col">');
    t.columns.forEach(col => {
      lines.push("      <div><ul>");
      col.forEach(i => lines.push("        <li>" + i + "</li>"));
      lines.push("      </ul></div>");
    });
    lines.push("    </div>");
  }
  if (t.callout) {
    const co = lg(t, "callout");
    const bt = co[1];
    const cls = bt === "tip" ? "tip-box" : "danger-box";
    lines.push('    <div class="' + cls + '">' + co[0] + "</div>");
  }
  lines.push("  </div>", "</div>");
  return lines.join("\n");
}

const CMAP = {
  "s-blue":  ["#1e40af", "#eff6ff", "#bfdbfe"],
  "s-red":   ["#991b1b", "#fef2f2", "#fecaca"],
  "s-green": ["#166534", "#f0fdf4", "#bbf7d0"],
  "s-amber": ["#92400e", "#fefce8", "#fde68a"],
  "s-purple":["#6b21a8", "#faf5ff", "#e9d5ff"],
  "s-slate": ["#334155", "#f1f5f9", "#cbd5e1"],
};
function renderBottomCard(t) {
  const c = CMAP[t.color] || CMAP["s-slate"];
  const tc = c[0], bg = c[1], bd = c[2];
  const ic = t.icon || "&#9679;", ttl = lg(t, "title");
  const lines = ['<div style="flex:1;background:' + bg + ';border:1.5px solid ' + bd + ';border-radius:5px;padding:5px 10px">',
    '  <strong style="color:' + tc + ';font-size:10.5px;text-transform:uppercase;letter-spacing:0.5px;">' + ic + " " + ttl + "</strong>",
    "  <ul style=\"margin-top:2px\">"];
  lg(t, "items").forEach(i => lines.push("    <li>" + i + "</li>"));
  if (t.callout) {
    const co = lg(t, "callout");
    const bt = co[1];
    const cls = bt === "tip" ? "tip-box" : "danger-box";
    lines.push('    <div class="' + cls + '" style="margin-top:3px">' + co[0] + "</div>");
  }
  lines.push("  </ul>", "</div>");
  return lines.join("\n");
}

function generate(weekNum, yearNow) {
  const year = yearNow || new Date().getFullYear();
  const monday = mondayOfWeek(weekNum, year);
  const friday = new Date(monday); friday.setDate(monday.getDate() + 4);
  const { left, right, bottom } = selectTopics(weekNum);

  const sheet = document.getElementById("sheet");
  const es = LANG === "es";
  const headerTitle = es ? "Reunión Semanal de Seguridad" : "Weekly Safety Huddle";
  const headerSub = es ? "Resumen de Seguridad del Conductor" : "Driver Safety Briefing";
  const footerTag = es ? "La Seguridad No Es una Prioridad — Es un Prerequisito" : "Safety is Not a Priority — It's a Prerequisite";
  const footerQ = es ? "¿Preguntas? Consulte a su Líder de Operaciones o Cumplimiento DOT." : "Questions? See your Operations Leader or DOT Compliance.";
  sheet.innerHTML =
    '<div class="header">' +
      '<img src="data:image/jpeg;base64,' + LOGO + '" alt="U.S. AutoForce">' +
      '<div class="header-text"><h1>' + headerTitle + '</h1><div class="subtitle">' + headerSub + '</div></div>' +
      '<div class="date-box"><div class="date">' + (es ? "Semana " : "Week ") + weekNum + "</div>" +
      "<div>" + fmtMD(monday) + " &mdash; " + fmtMDY(friday) + "</div></div>" +
    "</div>" +
    '<div class="grid-2"><div>' + left.map(renderSection).join("\n") + "</div><div>" +
    right.map(renderSection).join("\n") + "</div></div>" +
    '<div class="bottom-strip">' + bottom.map(renderBottomCard).join("\n") + "</div>" +
    '<div class="footer"><strong>U.S. AutoForce</strong> &middot; Field Operations &middot; ' +
    footerTag + "<br>" + footerQ + "</div>";

  document.getElementById("weekNum").value = weekNum;
  document.getElementById("rangeLabel").textContent =
    (es ? "Semana " : "Week ") + weekNum + " · " + fmtMD(monday) + " — " + fmtMDY(friday);
  document.title = (es ? "Seguridad — Semana " : "Safety Huddle — Week ") + weekNum;
  const langBtn = document.getElementById("langBtn");
  if (langBtn) langBtn.textContent = es ? "English" : "Español";
  af3dRefresh();
}

function currentWeek() { return isoWeek(new Date()); }

function buildPool() {
  const pool = document.getElementById("poolBody");
  const cols = [];
  for (let i = 0; i < TOPICS.length; i += 2) {
    const row = TOPICS.slice(i, i + 2).map(t =>
      '<div class="pool-card"><b class="chip ' + (t.color || "s-blue") + '">' + (t.icon || "&#9679;") + " " + lg(t, "title") +
      "</b><ul>" + lg(t, "items").map(x => "<li>" + x + "</li>").join("") +
      "</ul>" + (t.stat_cards ? t.stat_cards.map(s =>
        '<div class="pool-stat"><b>' + s[0] + "</b> " + s[1] + "</div>").join("") : "") +
      (t.columns ? t.columns.flat().map(x => "<li>" + x + "</li>").join("") : "") +
      (t.callout ? '<div class="' + (lg(t, "callout")[1] === "tip" ? "tip-box" : "danger-box") + '">' + lg(t, "callout")[0] + "</div>" : "") +
      "</div>").join("");
    cols.push('<div class="pool-col">' + row + "</div>");
  }
  pool.innerHTML = cols.join("");
  af3dRefresh();
}

function render() { generate(parseInt(document.getElementById("weekNum").value, 10) || currentWeek()); }

let zoom = 1;
function setZoom(v) {
  zoom = Math.max(0.5, Math.min(2, v));
  document.getElementById("sheetWrap").style.zoom = zoom;
  document.getElementById("zoomLabel").textContent = Math.round(zoom * 100) + "%";
}

function init() {
  const params = new URLSearchParams(window.location.search);
  const week = parseInt(params.get("week"), 10);
  document.getElementById("weekNum").value = week || currentWeek();
  generate(week || currentWeek(), new Date().getFullYear());
  buildPool();
  setZoom(1);

  document.getElementById("weekNum").addEventListener("change", render);
  document.getElementById("prevBtn").addEventListener("click", () => {
    document.getElementById("weekNum").value = (parseInt(document.getElementById("weekNum").value, 10) || 53) - 1;
    render(); setZoom(zoom);
  });
  document.getElementById("nextBtn").addEventListener("click", () => {
    document.getElementById("weekNum").value = (parseInt(document.getElementById("weekNum").value, 10) || 0) + 1;
    render(); setZoom(zoom);
  });
  document.getElementById("thisBtn").addEventListener("click", () => { render(); setZoom(zoom); });
  document.getElementById("zoomOutBtn").addEventListener("click", () => setZoom(zoom - 0.25));
  document.getElementById("zoomInBtn").addEventListener("click", () => setZoom(zoom + 0.25));
  document.getElementById("printBtn").addEventListener("click", () => {
    setZoom(1);
    setTimeout(() => window.print(), 60);
  });
  document.getElementById("poolBtn").addEventListener("click", function () {
    var pool = document.getElementById("pool");
    var open = getComputedStyle(pool).display === "none";
    pool.style.display = open ? "block" : "none";
    this.textContent = open ? (LANG === "es" ? "Ocultar Lista" : "Hide Topic Pool") : (LANG === "es" ? "Mostrar Lista" : "Show Topic Pool");
    if (open) af3dRefresh();
  });
  document.getElementById("langBtn").addEventListener("click", () => {
    LANG = LANG === "es" ? "en" : "es";
    localStorage.setItem("sh_lang", LANG);
    const pool = document.getElementById("pool");
    const poolOpen = getComputedStyle(pool).display !== "none";
    document.getElementById("poolBtn").textContent = poolOpen ? (LANG === "es" ? "Ocultar Lista" : "Hide Topic Pool") : (LANG === "es" ? "Mostrar Lista" : "Show Topic Pool");
    render(); setZoom(zoom); buildPool();
  });
}
document.addEventListener("DOMContentLoaded", init);
"""

CTRL_CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
body{background:#eef2f7;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:#1a1a2e}
.ctl{position:sticky;top:0;z-index:10;background:linear-gradient(135deg,#0b1120 0%,#1b2b4a 100%);color:#fff;
     padding:8px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;box-shadow:0 1px 8px rgba(0,0,0,.35)}
.ctl .brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:14px;letter-spacing:.4px}
.ctl .brand img{height:32px;width:auto;border-radius:5px}
.ctl .brand small{display:block;font-weight:400;font-size:10px;opacity:.75}
.ctl .spacer{flex:1}
.ctl label{font-size:10px;text-transform:uppercase;letter-spacing:.5px;opacity:.7}
.ctl input{width:64px;padding:3px 6px;border-radius:4px;border:1px solid #334155;font-size:14px;font-weight:600;text-align:center;color:#0b1120}
.ctl button{background:#2563eb;color:#fff;border:0;border-radius:5px;padding:6px 12px;font-size:12.5px;
            font-weight:600;cursor:pointer;letter-spacing:.3px}
.ctl button:hover{background:#1d4ed8}
.ctl button.ghost{background:transparent;border:1px solid rgba(255,255,255,.4)}
.ctl button.primary{background:#FFCD00;color:#0b1120}
.ctl button.primary:hover{background:#ffd633}
#rangeLabel{font-size:12px;opacity:.85;min-width:300px}
#zoomLabel{font-size:11px;opacity:.7;min-width:34px;text-align:center}
.tip{margin:8px 18px 0;font-size:11.5px;color:#475569;background:#fff;border:1px solid #e2e8f0;
     border-left:3px solid #2563eb;padding:6px 10px;border-radius:4px;display:inline-block}
#sheetWrap{margin:14px auto 40px;width:720px;transform-origin:top center}
#sheet{background:#fff;box-shadow:0 2px 18px rgba(0,0,0,.18);padding:12px 16px 10px}
#pool{display:none;max-width:1080px;margin:0 auto 40px;padding:10px;background:#fff;border-radius:8px;
      box-shadow:0 2px 14px rgba(0,0,0,.12)}
#pool h2{font-size:14px;margin:4px 6px 10px;color:#0b1120}
.pool-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.pool-card{border:1.5px solid #e2e8f0;border-radius:6px;padding:8px 10px}
.pool-card b.chip{font-size:12px;display:block;margin-bottom:4px;padding:2px 6px;border-radius:4px}
.chip.s-blue{background:#dbeafe;color:#1e40af}.chip.s-red{background:#fee2e2;color:#991b1b}
.chip.s-green{background:#dcfce7;color:#166534}.chip.s-amber{background:#fef3c7;color:#92400e}
.chip.s-purple{background:#f3e8ff;color:#6b21a8}.chip.s-slate{background:#f1f5f9;color:#334155}
.pool-card ul{padding-left:16px;font-size:11px}
.pool-card li{margin-bottom:1px}
.pool-stat{font-size:11px;color:#334155;margin:2px 0}
@media print{
  .ctl,.tip,#rangeLabel,#pool,#bg3d,.hud{display:none !important}
  body{background:#fff}
  #sheetWrap{zoom:1 !important;width:auto;margin:0;transform:none !important;animation:none !important}
  #sheet{box-shadow:none !important;padding:0 !important;position:static !important;overflow:visible !important}
  /* --- theme decorations must never reach the printed sheet --- */
  #sheet::before{display:none !important}
  #sheet .header{box-shadow:none !important}
  #sheet .header-text h1{text-shadow:none !important}
  #sheet .header .date-box .date{color:inherit !important;text-shadow:none !important}
  #sheet .header img{box-shadow:none !important}
  .section,.bottom-strip>div,.pool-card,.stat-card{
    transform:none !important;animation:none !important;box-shadow:none !important;transition:none !important}
  .section::after,.bottom-strip>div::after,.pool-card::after{display:none !important}
  .section:hover .stat-card,.stat-card:hover{transform:none !important;box-shadow:none !important}
  .stat-card .num{color:#0b1120 !important;text-shadow:none !important}
  .checklist li::before{transform:none !important;transition:none !important}
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
"""

# ---------------------------------------------------------------------------
# U.S. AutoForce "3D Command Deck" screen theme
# Palette sampled from the official logo: navy #1E2375 / brand red #E21D27,
# action gold #FFCD00.  Every 3D effect is pure CSS (no libraries, works
# offline).  The whole visual layer lives inside @media screen so the PRINTED
# huddle stays identical to the plain version.
# ---------------------------------------------------------------------------
THEME_CSS = r"""
.af3d{--af-indigo:#1E2375;--af-red:#E21D27;--af-gold:#FFCD00;--af-ice:#7dd3fc}

/* ---- background 3D scene (behind everything, fixed) ---- */
#bg3d{display:none}
.af3d #bg3d{display:block;position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
  perspective:2600px;perspective-origin:50% 46%;
  background:
    radial-gradient(ellipse 125% 78% at 50% 0%,#31497f 0%,#1a2750 34%,#0a1024 66%),
    linear-gradient(180deg,#080c18 0%,#101a36 48%,#06090f 100%)}
#bg3d .lyr{position:absolute;left:var(--x,50%);top:var(--y,50%);
  transform:translate(-50%,-50%)
            translate3d(calc(var(--px,0) * var(--d,0px)),
                        calc(var(--ny,0) * var(--d,0px)),0);
  will-change:transform}
/* ground-plane layers: their TOP edge sits on the horizon, so the parallax
   shift and the rotateX share one chain (rotate about the top-centre). */
#bg3d .lyr.horizon{transform-origin:50% 0;
  transform:translate3d(calc(-50% + var(--px,0) * var(--d,0px)),
                        calc(var(--ny,0) * var(--d,0px)),0) rotateX(-70deg)}
#bg3d .lyr.full{left:0;top:0;width:100%;height:100%;transform:none}

/* indigo halo + red brand sun, parked high so they show above the deck */
.af3d .bg-halo{width:1300px;height:1300px;border-radius:50%;
  background:radial-gradient(circle,rgba(30,35,117,.60) 0%,rgba(30,35,117,.16) 44%,transparent 68%);
  filter:blur(8px)}
.af3d .bg-sun{width:900px;height:900px;border-radius:50%;
  background:radial-gradient(circle,rgba(226,29,39,.42) 0%,rgba(226,29,39,.14) 40%,transparent 66%);
  filter:blur(4px);animation:sunPulse 7.5s ease-in-out infinite}
@keyframes sunPulse{0%,100%{opacity:.5}50%{opacity:1}}

/* perspective floor grid — wide enough to flank the 720px deck */
.af3d .bg-grid{width:5000px;height:9000px;opacity:1;
  background:
    repeating-linear-gradient(0deg,rgba(175,240,255,.95) 0 2px,transparent 2px 64px),
    repeating-linear-gradient(90deg,rgba(175,240,255,.95) 0 2px,transparent 2px 64px);
  -webkit-mask-image:linear-gradient(180deg,#000 0,rgba(0,0,0,.85) 50%,rgba(0,0,0,.50) 85%,rgba(0,0,0,.18) 100%);
  mask-image:linear-gradient(180deg,#000 0,rgba(0,0,0,.85) 50%,rgba(0,0,0,.50) 85%,rgba(0,0,0,.18) 100%);
  animation:gridRun 2.4s linear infinite}
@keyframes gridRun{from{background-position:0 0,0 0}to{background-position:0 64px,0 64px}}

/* bright horizon bar where the grid converges */
.af3d .bg-glow{width:5000px;height:300px;
  background:linear-gradient(180deg,rgba(160,230,255,.85),rgba(226,29,39,.45) 38%,transparent);
  filter:blur(3px)}

/* infinite 3D highway sitting on the same ground plane */
.af3d .bg-road{width:1400px;height:9000px;
  background:
    linear-gradient(90deg,rgba(255,255,255,.90) 0 10px,transparent 10px calc(100% - 10px),rgba(255,255,255,.90) calc(100% - 10px)),
    linear-gradient(180deg,rgba(255,205,0,.12) 0%,transparent 20%),
    linear-gradient(180deg,#2c4374 0%,#1d2d5c 50%,#131d40 100%);
  box-shadow:inset 0 0 300px rgba(0,0,0,.8)}
.af3d .bg-road .stripes{position:absolute;top:0;left:50%;width:44px;margin-left:-22px;height:9000px;
  background:repeating-linear-gradient(180deg,
    transparent 0 104px,rgba(255,205,0,.75) 104px 152px,transparent 152px 256px);
  animation:roadRun .55s linear infinite}
.af3d .bg-road .edges{position:absolute;top:0;left:0;right:0;height:9000px;
  background:linear-gradient(90deg,
    rgba(226,29,39,.70) 0 16px,transparent 16px calc(50% - 120px),
    rgba(226,29,39,.70) calc(50% + 104px) calc(50% + 120px),transparent calc(50% + 120px) calc(100% - 16px),
    rgba(226,29,39,.70) calc(100% - 16px));
  -webkit-mask-image:repeating-linear-gradient(180deg,#000 0 64px,transparent 64px 256px);
  mask-image:repeating-linear-gradient(180deg,#000 0 64px,transparent 64px 256px);
  animation:roadRun .55s linear infinite}
@keyframes roadRun{from{transform:translateY(0)}to{transform:translateY(256px)}}

/* vignette on top of the scene */
.af3d #bg3d .vig{position:absolute;inset:0;
  background:radial-gradient(ellipse 105% 95% at 50% 46%,transparent 58%,rgba(3,5,12,.45) 100%)}

/* ---- 3D logo cube in the control bar ---- */
.af3d .brand .cube{width:34px;height:34px;position:relative;transform-style:preserve-3d;--u:17px;
  flex:0 0 auto;animation:cubeSpin 11s linear infinite}
.af3d .brand .cube .f{position:absolute;inset:0;border-radius:5px;overflow:hidden;background:#0b1120;
  display:flex;align-items:center;justify-content:center;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.18),0 0 16px rgba(226,29,39,.28)}
.af3d .brand .cube .f img{width:30px;height:30px;object-fit:contain;background:#fff;border-radius:3px}
.af3d .brand .cube .f.red{background:linear-gradient(135deg,#E21D27 0%,#8f0d16 100%)}
.af3d .brand .cube .f.gold{background:linear-gradient(135deg,#FFCD00 0%,#b98f00 100%)}
.af3d .brand .cube .f.front {transform:translateZ(var(--u))}
.af3d .brand .cube .f.back  {transform:rotateY(180deg) translateZ(var(--u))}
.af3d .brand .cube .f.right {transform:rotateY(90deg)  translateZ(var(--u))}
.af3d .brand .cube .f.left  {transform:rotateY(-90deg) translateZ(var(--u))}
.af3d .brand .cube .f.top   {transform:rotateX(90deg)  translateZ(var(--u))}
.af3d .brand .cube .f.bottom{transform:rotateX(-90deg) translateZ(var(--u))}
@keyframes cubeSpin{from{transform:rotateX(-18deg) rotateY(0)}to{transform:rotateX(-18deg) rotateY(360deg)}}
.af3d .brand .cube:hover{animation-duration:2.2s}

/* 3D extruded control-bar text + reflective header edge */
.af3d .ctl{position:sticky;
  box-shadow:0 2px 0 rgba(226,29,39,.55),0 10px 30px rgba(0,0,0,.55)}
.af3d .ctl .brand>div{text-shadow:0 1px 0 rgba(255,255,255,.16),0 2px 0 rgba(0,0,0,.5),0 4px 10px rgba(0,0,0,.65)}
.af3d .ctl input{box-shadow:inset 0 2px 5px rgba(0,0,0,.45),0 0 0 1px rgba(255,205,0,.35)}
.af3d .ctl button{box-shadow:0 3px 0 rgba(0,0,0,.35);transition:transform .12s,box-shadow .12s,background .12s}
.af3d .ctl button:hover{transform:translateY(-2px);box-shadow:0 5px 0 rgba(0,0,0,.35)}
.af3d .ctl button:active{transform:translateY(1px);box-shadow:0 1px 0 rgba(0,0,0,.35)}
.af3d .ctl button.primary{background:linear-gradient(180deg,#FFCD00,#e0ac00);color:#0b1120;
  box-shadow:0 5px 0 #8f0d16,0 14px 26px rgba(226,29,39,.38);text-shadow:0 1px 0 rgba(255,255,255,.5)}
.af3d .ctl button.primary:hover{background:linear-gradient(180deg,#ffdb47,#f0bc00);
  box-shadow:0 7px 0 #8f0d16,0 20px 34px rgba(226,29,39,.5)}
.af3d .ctl button.primary:active{box-shadow:0 2px 0 #8f0d16}
.af3d .ctl button.on{background:var(--af-red);color:#fff;border-color:transparent;
  box-shadow:0 3px 0 #6d0912,0 0 16px rgba(226,29,39,.6)}

/* ---- floating 3D deck + HUD reticle ---- */
.af3d #sheetWrap{position:relative;z-index:2;animation:deckFloat 8.5s ease-in-out infinite}
@keyframes deckFloat{0%,100%{transform:translateY(0) rotateX(0)}
  50%{transform:translateY(-8px) rotateX(.8deg)}}
.af3d .hud{position:absolute;inset:-16px;pointer-events:none;z-index:4;background:
   linear-gradient(90deg,var(--af-gold),var(--af-gold)) 0 0/24px 2px no-repeat,
   linear-gradient(90deg,var(--af-gold),var(--af-gold)) 0 0/2px 24px no-repeat,
   linear-gradient(90deg,var(--af-red),var(--af-red)) 100% 0/24px 2px no-repeat,
   linear-gradient(90deg,var(--af-red),var(--af-red)) 100% 0/2px 24px no-repeat,
   linear-gradient(90deg,var(--af-red),var(--af-red)) 0 100%/24px 2px no-repeat,
   linear-gradient(90deg,var(--af-red),var(--af-red)) 0 100%/2px 24px no-repeat,
   linear-gradient(90deg,var(--af-gold),var(--af-gold)) 100% 100%/24px 2px no-repeat,
   linear-gradient(90deg,var(--af-gold),var(--af-gold)) 100% 100%/2px 24px no-repeat;
  filter:drop-shadow(0 0 6px rgba(255,205,0,.45))}
.af3d #sheet{position:relative;overflow:hidden;
  box-shadow:0 26px 60px rgba(2,5,14,.62),0 0 0 1px rgba(255,255,255,.06)}

/* radar sweep across the deck */
.af3d #sheet::before{content:'';position:absolute;left:0;right:0;top:0;height:150px;z-index:3;
  pointer-events:none;background:linear-gradient(180deg,rgba(255,205,0,.20),rgba(255,205,0,.05) 45%,transparent);
  animation:sweep 7s ease-in-out infinite}
@keyframes sweep{0%{transform:translateY(-160px)}60%,100%{transform:translateY(1000px)}}

/* 3D brand header inside the sheet */
.af3d #sheet .header{box-shadow:0 8px 22px rgba(2,5,14,.35);border-radius:8px}
.af3d #sheet .header-text h1{text-shadow:0 1px 0 rgba(255,255,255,.14),0 2px 6px rgba(0,0,0,.55)}
.af3d #sheet .header .date-box .date{color:var(--af-gold);text-shadow:0 0 12px rgba(255,205,0,.5)}
.af3d #sheet .header img{box-shadow:0 0 16px rgba(226,29,39,.35)}

/* ---- mouse-tracked 3D tilt on every card ---- */
.af3d .section,.af3d .bottom-strip>div,.af3d .pool-card{position:relative;
  transform:perspective(780px) rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg));
  transition:transform .16s ease-out,box-shadow .16s ease-out;will-change:transform}
.af3d .section:hover,.af3d .bottom-strip>div:hover,.af3d .pool-card:hover{
  box-shadow:0 14px 30px rgba(3,7,18,.30)}
.af3d .section::after,.af3d .bottom-strip>div::after,.af3d .pool-card::after{
  content:'';position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:0;
  transition:opacity .16s ease-out;
  background:radial-gradient(360px circle at var(--mx,50%) var(--my,50%),rgba(255,255,255,.60),transparent 62%)}
.af3d .section:hover::after,.af3d .bottom-strip>div:hover::after,.af3d .pool-card:hover::after{opacity:.55}
.af3d .bottom-strip>div::after{border-radius:5px}
.af3d .pool-card::after{border-radius:6px}

/* stat cards pop out of the deck */
.af3d .stat-card{transition:transform .16s ease-out,box-shadow .16s ease-out}
.af3d .section:hover .stat-card{transform:translateY(-2px) scale(1.045);box-shadow:0 6px 14px rgba(3,7,18,.22)}
.af3d .stat-card .num{color:var(--af-indigo);text-shadow:0 1px 0 rgba(255,255,255,.9)}

/* checklist boxes get a red hover fill */
.af3d .checklist li::before{transition:background .14s,border-color .14s,transform .14s}
.af3d .checklist li:hover::before{background:var(--af-red);border-color:var(--af-red);transform:scale(1.12)}

@media (prefers-reduced-motion:reduce){ .af3d *{animation:none !important} }
"""

# 3D behaviour: background parallax + per-card tilt.  All hoisted function
# declarations, so the main JS can call af3dRefresh() safely.
THEME_JS = r"""
const AF3D_MAX_TILT = 7;
const AF3D_TILT_SEL = ".section, .bottom-strip>div, .pool-card";

function af3dSet(on) {
  document.body.classList.toggle("af3d", on);
  var btn = document.getElementById("themeBtn");
  if (btn) { btn.textContent = on ? "3D Deck: On" : "3D Deck: Off"; btn.classList.toggle("on", on); }
  try { localStorage.setItem("af3d", on ? "1" : "0"); } catch (e) {}
  af3dRefresh();
}

function af3dParallax() {
  var bg = document.getElementById("bg3d");
  if (!bg) return;
  var raf = 0, tx = 0, ty = 0;
  function apply() {
    raf = 0;
    bg.style.setProperty("--px", tx.toFixed(3));
    bg.style.setProperty("--ny", (-ty).toFixed(3));
  }
  window.addEventListener("mousemove", function (e) {
    tx = (e.clientX / Math.max(1, window.innerWidth) - 0.5) * 2;
    ty = (e.clientY / Math.max(1, window.innerHeight) - 0.5) * 2;
    if (!raf) raf = requestAnimationFrame(apply);
  }, { passive: true });
}

function af3dRefresh() {
  if (!document.body.classList.contains("af3d")) return;
  var els = document.querySelectorAll(AF3D_TILT_SEL);
  for (var i = 0; i < els.length; i++) {
    (function (el) {
      if (el.dataset.tilt) return;
      el.dataset.tilt = "1";
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / Math.max(1, r.width);
        var py = (e.clientY - r.top) / Math.max(1, r.height);
        el.style.setProperty("--ry", ((px - 0.5) * 2 * AF3D_MAX_TILT).toFixed(2) + "deg");
        el.style.setProperty("--rx", ((0.5 - py) * 2 * AF3D_MAX_TILT).toFixed(2) + "deg");
        el.style.setProperty("--mx", (px * 100).toFixed(1) + "%");
        el.style.setProperty("--my", (py * 100).toFixed(1) + "%");
      }, { passive: true });
      el.addEventListener("mouseleave", function () {
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      });
    })(els[i]);
  }
}

function af3dInit() {
  var on = true;
  try { var s = localStorage.getItem("af3d"); if (s !== null) on = (s === "1"); } catch (e) {}
  af3dSet(on);
  var btn = document.getElementById("themeBtn");
  if (btn) btn.addEventListener("click", function () {
    af3dSet(!document.body.classList.contains("af3d"));
  });
  af3dParallax();
}
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>U.S. AutoForce — Safety Huddle Generator</title>
<style>
{CTRL_CSS}

{CSS}

{THEME_CSS}
</style>
</head>
<body class="af3d">
<div id="bg3d" aria-hidden="true">
  <div class="lyr bg-halo"  style="--x:50%;--y:16%;--d:14px"></div>
  <div class="lyr bg-sun"   style="--x:50%;--y:8%;--d:26px"></div>
  <div class="lyr horizon bg-grid" style="--x:50%;--y:46%;--d:6px"></div>
  <div class="lyr horizon bg-glow" style="--x:50%;--y:46%;--d:6px"></div>
  <div class="lyr horizon bg-road" style="--x:50%;--y:46%;--d:10px"><div class="stripes"></div><div class="edges"></div></div>
  <div class="lyr full vig"></div>
</div>
<header class="ctl">
  <div class="brand">
    <div class="cube" aria-hidden="true">
      <div class="f front"><img src="data:image/jpeg;base64,{LOGO}" alt=""></div>
      <div class="f back"><img src="data:image/jpeg;base64,{LOGO}" alt=""></div>
      <div class="f right"><img src="data:image/jpeg;base64,{LOGO}" alt=""></div>
      <div class="f left red"></div>
      <div class="f top red"></div>
      <div class="f bottom gold"></div>
    </div>
    <img src="data:image/jpeg;base64,{LOGO}" alt="U.S. AutoForce">
    <div>Safety Huddle Generator<small>Works offline &middot; Print &rarr; Save as PDF</small></div>
  </div>
  <div class="spacer"></div>
  <label for="weekNum">ISO Week</label>
  <input id="weekNum" type="number" min="1" max="53">
  <button class="ghost" id="prevBtn">&lsaquo; Prev</button>
  <button class="ghost" id="thisBtn">This Week</button>
  <button class="ghost" id="nextBtn">Next &rsaquo;</button>
  <button class="ghost" id="poolBtn">Show Topic Pool</button>
  <button class="ghost" id="langBtn" title="Switch language / Cambiar idioma">Español</button>
  <button class="ghost" id="zoomOutBtn" title="Zoom out">&minus;</button>
  <span id="zoomLabel">100%</span>
  <button class="ghost" id="zoomInBtn" title="Zoom in">+</button>
  <button class="ghost on" id="themeBtn" title="Toggle the 3D command-deck theme">3D Deck: On</button>
  <button class="primary" id="printBtn">Print / Save as PDF</button>
</header>
<div class="tip">Pick a week, then click <b>Print / Save as PDF</b> and choose &ldquo;Save as PDF&rdquo; as your printer. Tip: use <b>?week=N</b> in the address bar to jump to a specific week (e.g. file.html?week=42). The <b>3D Deck</b> look is screen-only &mdash; the printed sheet is always the clean one.</div>
<span id="rangeLabel" style="display:block;margin:8px 18px 0;font-size:12px;color:#94a3b8"></span>
<div id="sheetWrap"><div class="hud" aria-hidden="true"></div><div id="sheet"></div></div>
<div id="pool"><h2>Topic Pool (24 rotating topics)</h2><div class="pool-grid" id="poolBody"></div></div>
<script>
{JS}
{THEME_JS}
af3dInit();
</script>
</body>
</html>
"""

html = html.replace("__TOPICS_JSON__", TOPICS_JSON).replace("__LOGO__", LOGO)

OUT_DIR = os.path.expanduser("~/Desktop/work")
if not os.path.isdir(OUT_DIR):      # e.g. a fresh clone of this repo elsewhere
    OUT_DIR = HERE
out = os.path.join(OUT_DIR, "safety-huddle-generator.html")
with open(out, "w") as f:
    f.write(html)
print("wrote", out, len(html), "bytes")