# -*- coding: utf-8 -*-
"""Gallery for the hub site — links to each fish's landing page."""
import html
import care_fish as C
def esc(s): return html.escape(str(s))
def build(rows, SITE):
    groups=sorted(set(r["group"] for r in rows))
    cares=["Beginner","Beginner-Intermediate","Intermediate","Intermediate-Advanced","Advanced"]
    temps=["Peaceful","Peaceful (with care)","Semi-aggressive","Territorial","Aggressive"]
    cards=[]
    for p in sorted(rows,key=lambda x:(x["group"],x["common"])):
        cc=C.CARE_COLOR[p["care"]]; tc=C.TEMP_COLOR[p["temperament"]]
        cards.append(f'''<a class="fc" href="fish/{esc(p['slug'])}/"
 data-g="{esc(p['group'])}" data-c="{esc(p['care'])}" data-t="{esc(p['temperament'])}"
 data-s="{esc((p['common']+' '+p['group']+' '+p['title']).lower())}">
<div class="fc-top" style="border-color:{cc}"><div class="fc-name">{esc(p['common'])}</div>
<div class="fc-grp">{esc(p['group'])}</div></div>
<div class="fc-tags"><span class="t" style="background:{cc}">{esc(p['care'])}</span>
<span class="t" style="background:{tc}">{esc(p['temperament'])}</span></div>
<div class="fc-meta"><span>{esc(p['adult'])}</span><span>{esc(p['tank'])}</span></div></a>''')
    def opts(xs): return "".join(f'<option>{esc(x)}</option>' for x in xs)
    H=f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rakkad Aqua \u2014 Fish Care Sheets</title><style>
:root{{--deep:#0E4D5C;--aqua:#12A3AB;--mist:#F3F8F8;--line:#DCEAEA;--sub:#5B7375;--ink:#0B2027}}
*{{box-sizing:border-box}}body{{margin:0;font-family:'Inter','Segoe UI',Arial,sans-serif;background:#EAF2F2;color:var(--ink)}}
.top{{background:var(--deep);color:#EAF7F7;padding:18px 26px}}.top h1{{margin:0;font-size:20px}}
.top p{{margin:4px 0 0;opacity:.8;font-size:13px}}
.bar{{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line);padding:12px 26px;
display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.bar input,.bar select{{padding:9px 12px;border:1px solid var(--line);border-radius:9px;font-size:13px;background:var(--mist)}}
.bar input{{flex:1;min-width:200px}}.count{{font-size:12px;color:var(--sub);margin-left:auto;font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;padding:18px 26px}}
.fc{{display:flex;flex-direction:column;gap:8px;padding:12px;background:#fff;border:1px solid var(--line);
border-radius:12px;text-decoration:none;color:inherit;transition:.15s}}
.fc:hover{{box-shadow:0 4px 14px rgba(14,77,92,.13);transform:translateY(-2px)}}
.fc-top{{border-left:4px solid;padding-left:9px}}.fc-name{{font-weight:800;font-size:14.5px;line-height:1.2}}
.fc-grp{{font-size:11.5px;color:var(--aqua);font-weight:700;margin-top:2px}}
.fc-tags{{display:flex;gap:6px;flex-wrap:wrap}}
.fc-tags .t{{color:#fff;font-size:10px;font-weight:800;padding:2px 8px;border-radius:20px}}
.fc-meta{{display:flex;justify-content:space-between;font-size:11px;color:var(--sub);font-weight:600;
border-top:1px dashed var(--line);padding-top:7px}}
</style></head><body>
<div class="top"><h1>Rakkad Aqua \u2014 Fish Care Sheets</h1>
<p>{len(rows)} fish \u00b7 {len(groups)} care groups \u00b7 \u00b0C and litres \u00b7 feeding from the AQA range</p></div>
<div class="bar"><input id="q" placeholder="Search fish, group\u2026" oninput="flt()">
<select id="g" onchange="flt()"><option value="">All groups</option>{opts(groups)}</select>
<select id="c" onchange="flt()"><option value="">All care levels</option>{opts(cares)}</select>
<select id="t" onchange="flt()"><option value="">All temperaments</option>{opts(temps)}</select>
<span class="count" id="ct"></span></div>
<div class="grid">{''.join(cards)}</div>
<script>const cards=[...document.querySelectorAll('.fc')];
function flt(){{const q=document.getElementById('q').value.toLowerCase().trim();
const g=document.getElementById('g').value,c=document.getElementById('c').value,t=document.getElementById('t').value;let n=0;
cards.forEach(el=>{{const ok=(!q||el.dataset.s.includes(q))&&(!g||el.dataset.g===g)&&(!c||el.dataset.c===c)&&(!t||el.dataset.t===t);
el.style.display=ok?'':'none';if(ok)n++;}});document.getElementById('ct').textContent=n+' shown';}}
flt();</script></body></html>"""
    open(f"{SITE}/index.html","w").write(H)
