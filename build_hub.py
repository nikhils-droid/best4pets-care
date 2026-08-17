# -*- coding: utf-8 -*-
"""
Rakkad Aqua Hub — builds the hosting-ready site.

URL structure (QR codes already printed point at the landing page, so they stay valid):

  /fish/<slug>/            LANDING PAGE  <- the QR on every care sheet points here
                            shows two links: Care Guide + Check Price / Buy
  /fish/<slug>/care/       the full care sheet
  /fish/<handle>/          alias landing page keyed by Shopify product handle,
                            so order emails can link with {{ line_item.product.handle }}

Usage:
  python3 build_hub.py                 # build fresh from fish_classified.csv
  python3 build_hub.py master.csv      # rebuild from an edited master.csv (see editor.html)
"""
import os, sys, json, csv, re, html, shutil
import pandas as pd
import care_fish as C

SITE = "rakkad-aqua-hub-site"
HUB_BASE = "https://care.best4pets.in/fish/"      # <-- set to your live hub domain
SHOP_BASE = "https://best4pets.in/products/"       # <-- your Shopify product base

# --- pull helpers/templates/render() out of build_fish.py (everything above its build loop)
_src = open("build_fish.py").read().split('df=pd.read_csv')[0]
exec(_src)   # gives us: slugify, esc, meter, qr_datauri, qr_png, gal_to_litre, icon, CSS, PAGE, render
# build_fish.py also defines HUB_BASE — re-assert ours so it wins
HUB_BASE = "https://care.best4pets.in/fish/"
SHOP_BASE = "https://best4pets.in/products/"

# ------------------------------------------------------------------ records ---
def records_fresh():
    df = pd.read_csv("fish_classified.csv", dtype=str)
    out, n = [], 0
    for _, r in df.iterrows():
        title = r["Title"]; g = C.classify(title)
        if g is None or g not in C.GROUPS:
            continue
        n += 1
        env = C.apply_overrides(title, C.GROUPS[g])
        common = C.clean_name(title)
        p = dict(env)
        p["desc"] = env["desc"].replace("{n}", common)
        p["tank"] = gal_to_litre(p["tank"])
        p.update(group=g, common=common, slug=slugify(common), sku=f"RA-FSH-{n:04d}",
                 psize=C.parse_size(title), food=C.food_rec(g), title=title,
                 handle=str(r["Handle"]))
        out.append(p)
    return out

def records_from_master(path):
    by_handle = {v[1]: k for k, v in C.AQA_FOODS.items()}
    out = []
    for r in csv.DictReader(open(path)):
        p = dict(r)
        p["tips"] = [t.strip() for t in (r.get("tips") or "").split("|") if t.strip()]
        prim = by_handle.get(r.get("aqa_staple", ""), "colour")
        tre = by_handle.get(r.get("aqa_treat", ""), None)
        p["food"] = {"primary": C.AQA_FOODS[prim],
                     "treat": C.AQA_FOODS[tre] if tre else None,
                     "note": r.get("feeding_note", "")}
        out.append(p)
    return out

fish = records_from_master(sys.argv[1]) if len(sys.argv) > 1 else records_fresh()

# unique slugs
seen = {}
for p in fish:
    s = p["slug"]
    if s in seen:
        seen[s] += 1; p["slug"] = f"{s}-{seen[s]}"
    else:
        seen[s] = 1
for p in fish:
    p["hub_url"] = HUB_BASE + p["slug"]                    # QR target = landing page
    p["care_url"] = HUB_BASE + p["slug"] + "/care/"
    p["shop_url"] = SHOP_BASE + p["handle"] if p.get("handle") else ""

# ------------------------------------------------------------- landing page ---
LANDING = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} — Rakkad Aqua</title><style>
:root{{--deep:#0E4D5C;--aqua:#12A3AB;--mist:#F3F8F8;--line:#DCEAEA;--sub:#5B7375;--ink:#0B2027;--gold:#F2B33D}}
*{{box-sizing:border-box}}
body{{margin:0;background:#EAF2F2;font-family:'Inter','Segoe UI',Arial,sans-serif;color:var(--ink);
 display:flex;align-items:center;justify-content:center;min-height:100vh;padding:18px}}
.w{{width:100%;max-width:420px;background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;
 box-shadow:0 6px 26px rgba(14,77,92,.12)}}
.bb{{background:var(--deep);color:#EAF7F7;padding:13px 18px;display:flex;justify-content:space-between;
 font-size:10.5px;letter-spacing:.16em;font-weight:700}}
.bb .t{{opacity:.85;letter-spacing:.22em;font-weight:500}}
.hd{{padding:22px 20px 6px;border-left:7px solid {accent}}}
h1{{margin:0;font-size:23px;line-height:1.15;letter-spacing:-.01em}}
.grp{{color:var(--aqua);font-weight:700;font-size:12.5px;margin-top:3px}}
.meta{{color:var(--sub);font-size:12px;margin-top:5px}}
.q{{display:flex;gap:8px;flex-wrap:wrap;padding:12px 20px 4px}}
.q span{{font-size:10.5px;font-weight:800;color:#fff;border-radius:20px;padding:3px 10px}}
.btns{{padding:14px 20px 20px;display:flex;flex-direction:column;gap:10px}}
a.b{{display:flex;align-items:center;gap:12px;padding:15px 16px;border-radius:12px;text-decoration:none;
 font-weight:800;font-size:15px;transition:.15s}}
a.care{{background:var(--deep);color:#fff}}
a.shop{{background:var(--gold);color:#3A2B06}}
a.b:active{{transform:scale(.98)}}
a.b .ico{{font-size:19px}}
a.b .sub{{display:block;font-size:11px;font-weight:600;opacity:.85;margin-top:2px}}
.ft{{padding:12px 20px 16px;border-top:1px solid var(--line);color:var(--sub);font-size:10.5px;text-align:center}}
</style></head><body><div class="w">
<div class="bb"><span>RAKKAD AQUA</span><span class="t">AQUATIC FISH CARE</span></div>
<div class="hd"><h1>{name}</h1><div class="grp">{group}</div>
<div class="meta">{family} &nbsp;•&nbsp; Adult size {adult} &nbsp;•&nbsp; Min tank {tank}</div></div>
<div class="q"><span style="background:{accent}">{care}</span><span style="background:{tcol}">{temperament}</span></div>
<div class="btns">
  <a class="b care" href="{care_url}"><span class="ico">📖</span><span>Care Guide<span class="sub">Full care sheet — water, diet, tankmates</span></span></a>
  {shop_btn}
</div>
<div class="ft">Ref {sku} · Rakkad Aqua</div>
</div></body></html>"""

def landing_html(p):
    accent = C.CARE_COLOR[p["care"]]; tcol = C.TEMP_COLOR[p["temperament"]]
    shop = (f'<a class="b shop" href="{esc(p["shop_url"])}"><span class="ico">🛒</span>'
            f'<span>Check Price &amp; Buy<span class="sub">See live price and availability</span></span></a>'
            ) if p.get("shop_url") else ""
    return LANDING.format(name=esc(p["common"]), group=esc(p["group"]), family=esc(p["family"]),
        adult=esc(p["adult"]), tank=esc(p["tank"]), accent=accent, tcol=tcol,
        care=esc(p["care"]), temperament=esc(p["temperament"]),
        care_url=esc(p["care_url"]), shop_btn=shop, sku=esc(p["sku"]))

# ------------------------------------------------------------------- build ----
for _d in (f"{SITE}/fish", f"{SITE}/qr"):      # only clear generated dirs —
    if os.path.isdir(_d): shutil.rmtree(_d)      # never editor.html/IMPLEMENTATION.md/shopify/
os.makedirs(f"{SITE}/fish", exist_ok=True)
os.makedirs(f"{SITE}/qr", exist_ok=True)

alias = 0
for p in fish:
    d = f"{SITE}/fish/{p['slug']}"
    os.makedirs(f"{d}/care", exist_ok=True)
    open(f"{d}/index.html", "w").write(landing_html(p))                       # landing (QR target)
    open(f"{d}/care/index.html", "w").write(
        PAGE.format(title=esc(p["common"]), css=CSS, card=render(p)))         # care sheet
    qr_png(p["hub_url"], f"{SITE}/qr/{p['slug']}.png")
    h = p.get("handle") or ""
    if h and h != p["slug"]:                                                  # handle alias for emails
        os.makedirs(f"{SITE}/fish/{h}", exist_ok=True)
        open(f"{SITE}/fish/{h}/index.html", "w").write(landing_html(p)); alias += 1

# master.csv (now includes desc + tips + handle so everything is editable)
def flat(p):
    d = {k: v for k, v in p.items() if k not in ("food", "tips")}
    d["tips"] = " | ".join(p["tips"]) if isinstance(p["tips"], list) else p["tips"]
    d["aqa_staple"] = p["food"]["primary"][1]
    d["aqa_treat"] = p["food"]["treat"][1] if p["food"]["treat"] else ""
    d["feeding_note"] = p["food"]["note"]
    return d
cols = ["sku","slug","handle","common","group","family","origin","care","temperament","swim",
        "tank","adult","tempC","ph","hard","diet","social","life","psize","desc","tips",
        "aqa_staple","aqa_treat","feeding_note","hub_url","care_url","shop_url","title"]
rows = [flat(p) for p in fish]
with open(f"{SITE}/master.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    for r in rows: w.writerow(r)
json.dump(rows, open(f"{SITE}/master.json","w"), indent=1, ensure_ascii=False)

# species.json — the trimmed 16-field feed the Hub tank system reads.
# Emitted every build so a new fish in master.csv appears in the Hub after Sync.
SPECIES_FIELDS = ["slug","common","group","care","temperament","tank","adult","tempC",
                  "ph","hard","diet","social","handle","hub_url","shop_url","aqa_staple"]
species = [{k: r.get(k, "") for k in SPECIES_FIELDS} for r in rows]
json.dump(species, open(f"{SITE}/species.json","w"), indent=1, ensure_ascii=False)

# gallery
import index_hub
index_hub.build(rows, SITE)
print(f"site built: {len(fish)} fish | landing+care pages | {alias} handle aliases")
