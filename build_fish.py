# -*- coding: utf-8 -*-
"""Rakkad Aqua — Fish Care Sheet generator (same design language as plants)."""
import json, re, csv, base64, io, os, html
import pandas as pd, qrcode
import care_fish as C

BRAND="RAKKAD AQUA"; TAGLINE="AQUATIC FISH CARE"
HUB_BASE="https://care.best4pets.in/fish/"; OUT="fish_output"
for d in ("sheets","qr"): os.makedirs(f"{OUT}/{d}", exist_ok=True)

def slugify(s):
    s=s.lower().replace("'","").replace("\u2019","").replace('"','')
    return re.sub(r"[^a-z0-9]+","-",s).strip("-") or "fish"
def esc(s): return html.escape(str(s))
def meter(level,fill):
    return '<span class="meter">'+"".join(
        f'<span class="seg" style="background:{fill if i<level else "#E4EDED"}"></span>'
        for i in range(5))+'</span>'
def qr_datauri(url):
    img=qrcode.make(url,box_size=10,border=1,error_correction=qrcode.constants.ERROR_CORRECT_M)
    buf=io.BytesIO(); img.save(buf,format="PNG")
    return "data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
def qr_png(url,path):
    qrcode.make(url,box_size=10,border=2,error_correction=qrcode.constants.ERROR_CORRECT_M).save(path)

# gallons -> litres (standard aquarium tank equivalents, hobby-conventional)
_STD={5:20,10:40,15:55,20:75,29:110,30:115,40:150,50:190,55:200,75:280,90:340,
      120:450,125:475,150:570,180:680,200:760,250:950,300:1140}
def _g2l(g):
    g=int(g)
    if g in _STD: return _STD[g]
    l=g*3.785
    return int(round(l/5.0)*5) if l<200 else int(round(l/10.0)*10)
def gal_to_litre(s):
    s=re.sub(r'(\d+)\s*-\s*(\d+)(\+?)\s*gallons?',
             lambda m:f"{_g2l(m.group(1))}-{_g2l(m.group(2))}{m.group(3) or ''} L", s, flags=re.I)
    s=re.sub(r'(\d+)(\+?)\s*gallons?',
             lambda m:f"{_g2l(m.group(1))}{m.group(2) or ''} L", s, flags=re.I)
    return s

IC={
"fish":'<path d="M4 12c2.5-3.5 6-5 10-4.5 2 .3 3.8 1.4 5 2.5-1.2 1.1-3 2.2-5 2.5C10 13 6.5 15.5 4 12z"/><path d="M18.5 9l3-2v10l-3-2"/><circle cx="8" cy="11" r=".9" fill="currentColor" stroke="none"/>',
"cichlid":'<path d="M4 13c2-4 6-6 10-5 3 .7 5 2.5 6 4-1.5 1.6-3.6 3-6.6 3.5C9 16.2 6 16 4 13z"/><path d="M8 8.5c1.2-2 4-3 7-2.2M18.5 10l3-1.5v7l-3-1.5"/><circle cx="8.6" cy="12" r=".9" fill="currentColor" stroke="none"/>',
"catfish":'<path d="M3 13c3-2 7-2.6 11-1.2 2 .7 4 1.6 6 2.4M3 13c1.4 1.6 3.4 2.2 6.2 2.2M4 12.4c-1-.8-1.6-.9-2.6-.8M4 13.6c-1 .5-1.6.9-2.6 1"/><path d="M20 12.5l1.6-1v5l-1.6-1"/><circle cx="7" cy="12.6" r=".8" fill="currentColor" stroke="none"/>',
"betta":'<path d="M9.5 12c2-4 5-5.2 8-4.2-1 2-1 4.2 0 6.2-3 1.1-6 0-8-2z"/><path d="M9.5 12c-2 .8-4 1-6 3 2 .1 3.2 1.1 4 3 1-2 3.2-3.2 2-6zM9.5 12c-1.2-2-1.2-4.2 0-6"/><circle cx="14" cy="10.6" r=".8" fill="currentColor" stroke="none"/>',
"round":'<path d="M12 6c4 0 7 2.7 7 6s-3 6-7 6-7-2.7-7-6 3-6 7-6z"/><path d="M12 6c0-1.8-1-3-2-4M19 12l3-2v4l-3-2"/><circle cx="9" cy="11" r="1" fill="currentColor" stroke="none"/>',
"size":'<path d="M3 8.5h18v7H3zM7 8.5v3M11 8.5v4M15 8.5v3M19 8.5v4"/>',
"temp":'<path d="M12 14V4a2 2 0 0 1 4 0v10a4 4 0 1 1-4 0z"/><circle cx="14" cy="17" r="1.2" fill="currentColor" stroke="none"/>',
"ph":'<path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/>',
"hard":'<path d="M12 2l3 4-3 3-3-3 3-4zM6 10l3 4-3 3-3-3 3-4zM18 10l3 4-3 3-3-3 3-4z"/>',
"food":'<circle cx="7" cy="8" r="1.4"/><circle cx="12" cy="6.4" r="1.1"/><circle cx="16.4" cy="8.6" r="1.3"/><path d="M4 13c2.2 3 5 4.2 8 4.2s5.8-1.2 8-4.2"/>',
"group":'<circle cx="7.5" cy="9" r="2.3"/><circle cx="15" cy="8" r="1.9"/><circle cx="12" cy="15.5" r="2.2"/>',
"tank":'<rect x="3" y="6" width="18" height="13" rx="1.6"/><path d="M3 9.5h18M6 12.5c2 1.6 4 1.6 6 0s4-1.6 6 0"/>',
"temperament":'<path d="M13 3l-6 9h5l-1 9 7-11h-5z"/>',
"swim":'<path d="M8 4v16M8 4L5.2 7M8 4l2.8 3M16 20V4M16 20l-2.8-3M16 20l2.8-3"/>',
"life":'<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
"tip":'<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10c1 1 1.5 2 1.5 3h5c0-1 .5-2 1.5-3a6 6 0 0 0-4-10z"/>',
"pin":'<path d="M12 21s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11z"/><circle cx="12" cy="10" r="2.4"/>',
}
def icon(name,size=18,cls=""):
    return (f'<svg class="ic {cls}" viewBox="0 0 24 24" width="{size}" height="{size}" '
            f'fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{IC.get(name,IC["fish"])}</svg>')
GROUP_ICON={"Angelfish":"cichlid","Discus":"cichlid","Dwarf Cichlid (Apisto/Ram)":"cichlid",
 "African Rift Cichlid (Malawi)":"cichlid","Tanganyikan Cichlid":"cichlid","Eartheater/Geophagus":"cichlid",
 "SA/CA Cichlid (large)":"cichlid","Cichlid (other)":"cichlid","Pleco (L-number/Bristlenose)":"catfish",
 "Corydoras":"catfish","Otocinclus":"catfish","Catfish (other)":"catfish","Loach":"catfish",
 "Hillstream Loach":"catfish","Betta":"betta","Gourami/Anabantid":"betta","Goldfish":"round","Koi":"round"}
def group_icon(g): return GROUP_ICON.get(g,"fish")

CSS=open("build.py").read().split('CSS = """',1)[1].split('"""',1)[0]
CSS+="""
.feed{margin:12px 22px 0;padding:12px 14px;border:1px solid var(--line);border-radius:11px;
  background:color-mix(in srgb,var(--accent) 6%,#fff)}
.feed .h{margin-bottom:8px}
.feedrow{display:flex;gap:9px;align-items:baseline;padding:3px 0}
.feedrow .fp{font-weight:800;color:var(--deep);font-size:12.5px;flex:0 0 auto}
.feedrow .role{font-size:9.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
  color:#fff;background:var(--accent);border-radius:5px;padding:2px 6px;flex:0 0 auto}
.feedrow .role.treat{background:var(--gold)}
.feedrow .fd{color:var(--sub);font-size:11.5px}
.fnote{font-size:11px;color:#7a5a12;background:#FBF3DF;border-radius:7px;padding:6px 9px;
  margin-top:6px;border:1px solid #F0E1B8}
.req .rv.big{font-size:15px}
"""
PAGE="""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} \u2014 Rakkad Aqua Fish Care</title><style>{css}
body{{margin:0;padding:18px;background:#E9F1F1}}</style></head><body>{card}</body></html>"""

def render(p):
    accent=C.CARE_COLOR[p["care"]]; tcol=C.TEMP_COLOR[p["temperament"]]
    tips="".join(f"<li>{esc(t)}</li>" for t in p["tips"]); f=p["food"]
    fr=f'<div class="feedrow"><span class="role">Staple</span><span class="fp">{esc(f["primary"][0])}</span><span class="fd">{esc(f["primary"][2])}</span></div>'
    if f["treat"]:
        fr+=f'<div class="feedrow"><span class="role treat">Treat</span><span class="fp">{esc(f["treat"][0])}</span><span class="fd">{esc(f["treat"][2])}</span></div>'
    if f["note"]:
        fr+=f'<div class="fnote">{esc(f["note"])}</div>'
    psize=f' &nbsp;\u00b7&nbsp; Ships at ~{esc(p["psize"])}' if p["psize"] else ""
    return f"""<div class="card" style="--accent:{accent}">
  <div class="brandbar"><span class="wm">{BRAND}</span><span class="tag">{TAGLINE}</span></div>
  <div class="hero">
    <div class="badge" style="color:{accent}">{icon(group_icon(p['group']),30)}</div>
    <div class="htext">
      <h1 class="common">{esc(p['common'])}</h1>
      <div class="sci" style="font-style:normal">{esc(p['group'])}</div>
      <div class="meta">{esc(p['family'])} &nbsp;\u2022&nbsp; Origin: {esc(p['origin'])} &nbsp;\u2022&nbsp; Lifespan: {esc(p['life'])}</div>
    </div>
  </div>
  <div class="chips">
    <span class="chip diff" style="background:{accent}">{icon('pin',13)}{esc(p['care'])}</span>
    <span class="chip diff" style="background:{tcol}">{icon('temperament',13)}{esc(p['temperament'])}</span>
    <span class="chip">{icon('swim',13)}{esc(p['swim'])}</span>
  </div>
  <div class="reqs">
    <div class="req"><span class="rl">Care Level</span>{meter(C.CARE_LVL[p['care']],accent)}<span class="rv">{esc(p['care'])}</span></div>
    <div class="req"><span class="rl">Temperament</span>{meter(C.TEMP_LVL[p['temperament']],tcol)}<span class="rv">{esc(p['temperament'])}</span></div>
    <div class="req"><span class="rl">Min Tank Size</span><span class="rv big">{esc(p['tank'])}</span></div>
  </div>
  <div class="grid">
    <div class="tile">{icon('size',18)}<div><div class="tk">Adult Size</div><div class="tv">{esc(p['adult'])}</div></div></div>
    <div class="tile">{icon('temp',18)}<div><div class="tk">Temperature</div><div class="tv">{esc(p['tempC'])}</div></div></div>
    <div class="tile">{icon('ph',18)}<div><div class="tk">pH Range</div><div class="tv">{esc(p['ph'])}</div></div></div>
    <div class="tile">{icon('hard',18)}<div><div class="tk">Water Hardness</div><div class="tv">{esc(p['hard'])}</div></div></div>
    <div class="tile">{icon('food',18)}<div><div class="tk">Diet</div><div class="tv">{esc(p['diet'])}</div></div></div>
    <div class="tile">{icon('group',18)}<div><div class="tk">Social &amp; Grouping</div><div class="tv">{esc(p['social'])}</div></div></div>
  </div>
  <div class="sec"><div class="h">{icon('pin',14)}About this fish</div><p class="desc">{esc(p['desc'])}</p></div>
  <div class="sec"><div class="h">{icon('tip',14)}Care tips</div><ul class="tips">{tips}</ul></div>
  <div class="feed"><div class="h">{icon('food',14)}Recommended feeding \u00b7 AQA range</div>{fr}</div>
  <div class="foot">
    <div class="fl"><b>{BRAND}</b> &nbsp;\u00b7&nbsp; Aquatic Fish Care &nbsp;\u00b7&nbsp; Ref {esc(p['sku'])}{psize}</div>
    <div class="qr"><div class="qc"><b>SCAN</b>full care guide on the Rakkad Aqua hub</div>
      <img src="{qr_datauri(p['hub_url'])}" alt="QR"></div>
  </div>
</div>"""

df=pd.read_csv("fish_classified.csv",dtype=str)
fish,review,n=[],[],0
for _,r in df.iterrows():
    title=r["Title"]; g=C.classify(title)
    if g is None or g not in C.GROUPS:
        review.append({"title":title,"purchase_size":C.parse_size(title),"vendor":r.get("Vendor","")}); continue
    n+=1; env=C.apply_overrides(title,C.GROUPS[g]); common=C.clean_name(title)
    p=dict(env); p["desc"]=env["desc"].replace("{n}",common)
    p.update(group=g,common=common,slug=slugify(common),sku=f"RA-FSH-{n:04d}",
        psize=C.parse_size(title),food=C.food_rec(g),title=title)
    p["tank"]=gal_to_litre(p["tank"])
    p["hub_url"]=HUB_BASE+p["slug"]; fish.append(p)
seen={}
for p in fish:
    s=p["slug"]
    if s in seen: seen[s]+=1; p["slug"]=f"{s}-{seen[s]}"; p["hub_url"]=HUB_BASE+p["slug"]
    else: seen[s]=1
for p in fish:
    open(f"{OUT}/sheets/{p['slug']}.html","w").write(PAGE.format(title=esc(p["common"]),css=CSS,card=render(p)))
    qr_png(p["hub_url"],f"{OUT}/qr/{p['slug']}.png")
def flat(p):
    d={k:v for k,v in p.items() if k not in ("food","tips")}
    d["tips"]=" | ".join(p["tips"]); d["aqa_staple"]=p["food"]["primary"][1]
    d["aqa_treat"]=p["food"]["treat"][1] if p["food"]["treat"] else ""; d["feeding_note"]=p["food"]["note"]; return d
master=[flat(p) for p in fish]
json.dump(master,open(f"{OUT}/master.json","w"),indent=1,ensure_ascii=False)
cols=["sku","slug","common","group","family","origin","care","temperament","swim","tank","adult",
      "tempC","ph","hard","diet","social","life","psize","aqa_staple","aqa_treat","feeding_note","hub_url","title"]
with open(f"{OUT}/master.csv","w",newline="") as fp:
    w=csv.DictWriter(fp,fieldnames=cols,extrasaction="ignore"); w.writeheader()
    for d in master: w.writerow(d)
with open(f"{OUT}/review.csv","w",newline="") as fp:
    w=csv.DictWriter(fp,fieldnames=["title","purchase_size","vendor"]); w.writeheader()
    for d in review: w.writerow(d)
json.dump({"fish":fish},open(f"{OUT}/_fish.json","w"),default=str)
print(f"Built {len(fish)} fish sheets + QR.  Review(manual): {len(review)}.  Groups used: {len(set(p['group'] for p in fish))}")
