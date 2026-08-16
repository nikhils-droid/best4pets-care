# -*- coding: utf-8 -*-
"""
Rakkad Aqua — Aquatic Plant Care Sheet generator.
Single source of truth for the care-sheet DESIGN LANGUAGE + a templating engine
that emits one self-contained HTML card per species (QR-ready for the hub, and
printable / shareable as a single file). Also emits index.html, master.json,
master.csv, and per-plant QR PNGs.
"""
import json, re, csv, base64, io, os, html
import qrcode
import qrcode.image.svg
from care_data import CARE

# ------------------------------------------------------------------ config ----
BRAND = "RAKKAD AQUA"
TAGLINE = "AQUATIC PLANT CARE"
# Change this to your live hub path; QR codes on each card point to BASE + slug
HUB_BASE = "https://care.best4pets.in/plants/"
OUT = "output"
os.makedirs(f"{OUT}/sheets", exist_ok=True)
os.makedirs(f"{OUT}/qr", exist_ok=True)

# ------------------------------------------------------------------ helpers ---
def slugify(s):
    s = s.lower()
    s = s.replace("'", "").replace("’", "").replace("(", "").replace(")", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

DIFF_LVL = {"Easy":1,"Easy-Medium":2,"Medium":3,"Medium-Advanced":4,"Advanced":5}
LIGHT_LVL = {"Low":1,"Low-Medium":2,"Medium":3,"Medium-High":4,"High":5}
CO2_LVL = {"Not required":1,"Beneficial":2,"Recommended":4,"Required":5}
DIFF_COLOR = {"Easy":"#2FA36B","Easy-Medium":"#6FB05A","Medium":"#E0972B",
              "Medium-Advanced":"#D9702C","Advanced":"#C6482E"}

def category(habit, placement):
    p = placement.lower()
    if "floating" in p: return "Floating"
    if "emersed" in p or "bog" in p: return "Bog / Emersed"
    if "epiphyte" in p and habit not in ("Moss",): return "Epiphyte"
    return {"Stem":"Stem","Rosette":"Rosette","Moss":"Moss",
            "Grass":"Grass / Carpet","Floater":"Floating"}.get(habit, habit)

# -------- minimal inline SVG icons (stroke = currentColor, weasyprint-safe) ---
IC = {
"Stem":'<path d="M12 21V7M12 7c0-3 3-4 5-4M12 11c0-2-3-3-5-3M12 15c0-2 3-3 5-3"/>',
"Rosette":'<path d="M12 12c0-4 3-7 3-7M12 12c0 4 3 7 3 7M12 12c-4 0-7 3-7 3M12 12c4 0 7 3 7 3M12 12c0-4-3-7-3-7M12 12c-4 0-7-3-7-3"/>',
"Moss":'<circle cx="8" cy="14" r="2"/><circle cx="13" cy="11" r="2.3"/><circle cx="17" cy="15" r="2"/><path d="M4 20h16"/>',
"Grass / Carpet":'<path d="M4 21c1-6 2-9 3-11M9 21c0-6 0-10 1-13M14 21c0-6 1-9 2-12M19 21c-1-5-1-8 0-11"/>',
"Floating":'<ellipse cx="12" cy="9" rx="7" ry="3.2"/><path d="M12 12v7M9 14l-1 5M15 14l1 5M5 21h14"/>',
"Epiphyte":'<path d="M3 20h18M6 20c0-4 2-7 6-7s6 3 6 7M12 13V6M12 6c0-2 2-3 4-3"/>',
"Bog / Emersed":'<path d="M4 16h16M4 16c2-1 4-1 8 0s6 1 8 0M10 16c0-4 1-6 2-8M14 16c0-3-1-5-2-7"/>',
"light":'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/>',
"co2":'<circle cx="8" cy="15" r="2.4"/><circle cx="14" cy="9" r="1.6"/><circle cx="16" cy="16" r="1.2"/>',
"rate":'<path d="M12 12l4-4M4 20a10 10 0 0 1 16 0"/><circle cx="12" cy="12" r="1.4"/>',
"height":'<path d="M12 3v18M12 3l-3 3M12 3l3 3M12 21l-3-3M12 21l3-3M5 3h4M5 21h4"/>',
"temp":'<path d="M12 14V4a2 2 0 0 1 4 0v10a4 4 0 1 1-4 0z"/><circle cx="14" cy="17" r="1.2" fill="currentColor" stroke="none"/>',
"ph":'<path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/>',
"hard":'<path d="M12 2l3 4-3 3-3-3 3-4zM6 10l3 4-3 3-3-3 3-4zM18 10l3 4-3 3-3-3 3-4z"/>',
"prop":'<path d="M12 22V10M12 10c0-3-2-5-5-5M12 10c0-3 2-5 5-5M7 5a2 2 0 1 0 0-.01M17 5a2 2 0 1 0 0-.01"/>',
"tip":'<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10c1 1 1.5 2 1.5 3h5c0-1 .5-2 1.5-3a6 6 0 0 0-4-10z"/>',
"pin":'<path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.4"/>',
}
def icon(name, size=18, cls=""):
    body = IC.get(name, IC["Stem"])
    return (f'<svg class="ic {cls}" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>')

def meter(level, fill):
    segs = "".join(
        f'<span class="seg" style="background:{fill if i < level else "#E4EDED"}"></span>'
        for i in range(5))
    return f'<span class="meter">{segs}</span>'

def qr_datauri(url):
    img = qrcode.make(url, box_size=10, border=1,
                      error_correction=qrcode.constants.ERROR_CORRECT_M)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def qr_png(url, path):
    qrcode.make(url, box_size=10, border=2,
                error_correction=qrcode.constants.ERROR_CORRECT_M).save(path)

def esc(s): return html.escape(str(s))

# ----------------------------------------------------------- shared CSS -------
CSS = """
:root{
  --ink:#0B2027; --deep:#0E4D5C; --aqua:#12A3AB; --aqua-2:#0E8890;
  --mist:#F3F8F8; --panel:#FFFFFF; --line:#DCEAEA; --sub:#5B7375;
  --gold:#F2B33D; --tip:#0E8890;
}
*{box-sizing:border-box}
.card{
  --accent:var(--aqua);
  width:210mm; max-width:820px; margin:0 auto; background:var(--panel);
  color:var(--ink); font-family:'Inter','Segoe UI',Helvetica,Arial,sans-serif;
  font-size:13px; line-height:1.5; position:relative;
  border:1px solid var(--line); border-radius:14px; overflow:hidden;
}
.brandbar{
  display:flex; align-items:center; justify-content:space-between;
  padding:11px 22px; background:var(--deep); color:#EAF7F7;
  letter-spacing:.16em; font-size:11px; font-weight:600;
}
.brandbar .wm{font-weight:800; letter-spacing:.22em}
.brandbar .tag{opacity:.85; letter-spacing:.28em; font-weight:500}
.hero{display:flex; gap:16px; padding:20px 22px 14px; align-items:flex-start;
  border-left:7px solid var(--accent);}
.badge{flex:0 0 auto; width:52px; height:52px; border-radius:13px;
  background:var(--mist); color:var(--accent); display:flex; align-items:center;
  justify-content:center; border:1px solid var(--line);}
.badge svg{width:30px;height:30px}
.htext{flex:1 1 auto; min-width:0}
.common{font-size:23px; font-weight:800; line-height:1.15; letter-spacing:-.01em;
  color:var(--ink); margin:0 0 2px}
.sci{font-style:italic; color:var(--aqua-2); font-weight:600; font-size:14px}
.meta{color:var(--sub); font-size:12px; margin-top:3px}
.chips{display:flex; flex-wrap:wrap; gap:7px; padding:0 22px 14px}
.chip{display:inline-flex; align-items:center; gap:5px; padding:4px 11px;
  border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.02em;
  background:var(--mist); color:var(--deep); border:1px solid var(--line);}
.chip.diff{color:#fff; border:none}
.chip .ic{width:13px;height:13px}
.reqs{display:flex; gap:10px; padding:10px 22px 2px}
.req{flex:1; display:flex; flex-direction:column; gap:6px; padding:10px 13px;
  background:var(--mist); border:1px solid var(--line); border-radius:10px}
.req .rl{font-size:10px; text-transform:uppercase; letter-spacing:.08em;
  color:var(--sub); font-weight:700}
.req .rv{font-size:12px; font-weight:800; color:var(--ink)}
.meter{display:inline-flex; gap:3px; vertical-align:middle}
.meter .seg{width:15px; height:7px; border-radius:2px; display:inline-block}
.grid{display:grid; grid-template-columns:1fr 1fr 1fr; gap:1px;
  background:var(--line); margin:12px 22px 0; border:1px solid var(--line);
  border-radius:11px; overflow:hidden}
.tile{background:var(--panel); padding:11px 13px; display:flex; gap:9px;
  align-items:flex-start}
.tile .ic{color:var(--accent); flex:0 0 auto; margin-top:1px}
.tk{font-size:10px; text-transform:uppercase; letter-spacing:.07em;
  color:var(--sub); font-weight:700}
.tv{font-size:13px; font-weight:700; color:var(--ink); line-height:1.25; margin-top:1px}
.sec{padding:14px 22px 0}
.h{display:flex; align-items:center; gap:7px; font-size:11px; font-weight:800;
  letter-spacing:.11em; text-transform:uppercase; color:var(--deep); margin:0 0 6px}
.h .ic{color:var(--accent)}
.desc{color:#23383A; font-size:12.5px; margin:0}
.tips{list-style:none; margin:6px 0 0; padding:0}
.tips li{position:relative; padding:4px 0 4px 22px; font-size:12.5px; color:#23383A}
.tips li::before{content:""; position:absolute; left:2px; top:9px; width:9px;
  height:9px; border-radius:50%; background:var(--accent);
  box-shadow:0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent)}
.foot{display:flex; align-items:center; justify-content:space-between; gap:14px;
  margin:16px 0 0; padding:14px 22px; background:var(--mist);
  border-top:1px solid var(--line)}
.foot .fl{font-size:10.5px; color:var(--sub); line-height:1.55}
.foot .fl b{color:var(--deep); font-weight:800; letter-spacing:.04em}
.foot .fl a{color:var(--aqua-2); text-decoration:none; word-break:break-all}
.qr{display:flex; align-items:center; gap:10px; flex:0 0 auto}
.qr img{width:74px; height:74px; border:4px solid #fff; border-radius:8px;
  box-shadow:0 1px 4px rgba(0,0,0,.1)}
.qr .qc{font-size:9.5px; color:var(--sub); text-align:right; max-width:96px;
  line-height:1.4; font-weight:600}
.qr .qc b{color:var(--deep); display:block; font-size:10.5px; letter-spacing:.05em}
@media print{
  body{margin:0; background:#fff !important}
  .card{border:none; border-radius:0; width:auto; max-width:none}
  a{color:inherit !important}
}
@page{size:A4; margin:8mm}
"""

# --------------------------------------------------------- card template ------
def render_card(p):
    accent = DIFF_COLOR[p["difficulty"]]  # accent keyed to difficulty tier
    cat = p["category"]
    tips = "".join(f"<li>{esc(t)}</li>" for t in p["tips"])
    qr = qr_datauri(p["hub_url"])
    return f"""<div class="card" style="--accent:{accent}">
  <div class="brandbar"><span class="wm">{BRAND}</span><span class="tag">{TAGLINE}</span></div>
  <div class="hero">
    <div class="badge" style="color:{accent}">{icon(cat,30)}</div>
    <div class="htext">
      <h1 class="common">{esc(p['common'])}</h1>
      <div class="sci">{esc(p['species'])}{('  ·  ' + esc(p['syn'])) if p.get('syn') else ''}</div>
      <div class="meta">{esc(p['family'])} &nbsp;•&nbsp; Origin: {esc(p['origin'])}</div>
    </div>
  </div>
  <div class="chips">
    <span class="chip diff" style="background:{accent}">{icon('pin',13)}{esc(p['difficulty'])}</span>
    <span class="chip">{icon(cat,13)}{esc(cat)}</span>
    <span class="chip">{esc(p['placement'])}</span>
  </div>
  <div class="reqs">
    <div class="req"><span class="rl">Difficulty</span>{meter(DIFF_LVL[p['difficulty']],accent)}<span class="rv">{esc(p['difficulty'])}</span></div>
    <div class="req"><span class="rl">Light</span>{meter(LIGHT_LVL[p['light']],'var(--gold)')}<span class="rv">{esc(p['light'])}</span></div>
    <div class="req"><span class="rl">CO₂</span>{meter(CO2_LVL[p['co2']],'var(--aqua)')}<span class="rv">{esc(p['co2'])}</span></div>
  </div>
  <div class="grid">
    <div class="tile">{icon('rate',18)}<div><div class="tk">Growth Rate</div><div class="tv">{esc(p['rate'])}</div></div></div>
    <div class="tile">{icon('height',18)}<div><div class="tk">Height</div><div class="tv">{esc(p['height'])}</div></div></div>
    <div class="tile">{icon('temp',18)}<div><div class="tk">Temperature</div><div class="tv">{esc(p['temp'])}</div></div></div>
    <div class="tile">{icon('ph',18)}<div><div class="tk">pH Range</div><div class="tv">{esc(p['ph'])}</div></div></div>
    <div class="tile">{icon('hard',18)}<div><div class="tk">Hardness</div><div class="tv">{esc(p['gh'])}</div></div></div>
    <div class="tile">{icon('prop',18)}<div><div class="tk">Propagation</div><div class="tv">{esc(p['prop'])}</div></div></div>
  </div>
  <div class="sec">
    <div class="h">{icon('pin',14)}About this plant</div>
    <p class="desc">{esc(p['desc'])}</p>
  </div>
  <div class="sec">
    <div class="h">{icon('tip',14)}Care tips</div>
    <ul class="tips">{tips}</ul>
  </div>
  <div class="foot">
    <div class="fl">
      <b>{BRAND}</b> &nbsp;·&nbsp; Aquatic Plant Care &nbsp;·&nbsp; Ref {esc(p['sku'])}
    </div>
    <div class="qr">
      <div class="qc"><b>SCAN</b>full care guide on the Rakkad Aqua hub</div>
      <img src="{qr}" alt="QR to care guide">
    </div>
  </div>
</div>"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Rakkad Aqua Care Guide</title>
<style>{css}
body{{margin:0; padding:18px; background:#E9F1F1;}}
</style></head><body>{card}</body></html>"""

# ------------------------------------------------------------------ build -----
sheet = {r["sno"]: r for r in json.load(open("sheet.json"))}
plants = []
for sno, c in sorted(CARE.items()):
    s = sheet[sno]
    slug = slugify(s["species"])
    p = dict(c)
    p.update(sno=sno, species=s["species"], explant=s["explant"], habit=s["habit"],
             container=s["container"], price=s["price"], ref=s["ref"],
             slug=slug, sku=f"RA-AQ-{sno:03d}", hub_url=HUB_BASE + slug)
    p["category"] = category(s["habit"], p["placement"])
    plants.append(p)

# individual HTML cards + QR pngs
for p in plants:
    card = render_card(p)
    open(f"{OUT}/sheets/{p['slug']}.html","w").write(
        PAGE.format(title=esc(p["common"]), css=CSS, card=card))
    qr_png(p["hub_url"], f"{OUT}/qr/{p['slug']}.png")

# master data exports
json.dump(plants, open(f"{OUT}/master.json","w"), indent=1, ensure_ascii=False)
cols = ["sno","sku","slug","common","species","family","origin","category","habit",
        "placement","difficulty","light","co2","rate","height","spread","temp","ph",
        "gh","prop","explant","container","price","hub_url","ref","desc"]
with open(f"{OUT}/master.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for p in plants: w.writerow(p)

print(f"Built {len(plants)} care sheets + QR codes.")
print("Sample:", plants[0]["slug"], "|", plants[87]["slug"])
