# Rakkad Aqua — care site (auto-publishing)

This repo builds care.best4pets.in. On every commit, Netlify runs the generator
and publishes the fresh site — no more drag-and-drop.

## What's here
- master.csv ............ source of truth (edit this via editor.html)
- build_hub.py + build_fish.py + care_fish.py + index_hub.py + build.py .. generator
- fish_classified.csv ... fallback data for a "fresh" build
- netlify.toml ......... build command + publish folder
- requirements.txt / runtime.txt .. Python deps + version

## How a change goes live (once connected)
1. Edit a fish in editor.html -> Export master.csv
2. Replace master.csv in this repo (commit it)
3. Netlify runs `python3 build_hub.py master.csv` and publishes automatically

## Build settings (already in netlify.toml)
- Build command: pip install -r requirements.txt && python3 build_hub.py master.csv
- Publish directory: rakkad-aqua-hub-site
