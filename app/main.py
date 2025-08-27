# app/main.py
# Minimalna wyrocznia: /health, /oracle?n=..., oraz strona główna z formularzem.
# Czyta treści z app/oracle.json i codziennie zmienia przyporządkowanie liczb (bez losowania przy żądaniu).

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json, os, hmac, hashlib, random

# ---- konfiguracja ----
APP_TZ = os.getenv("APP_TZ", "Europe/Warsaw")
SECRET_SALT = os.getenv("SECRET_SALT", "domyslny_klucz")  # ustaw w Render → Settings → Environment

# ---- wczytanie talii ----
DECK_PATH = Path(__file__).with_name("oracle.json")
DECK = json.loads(DECK_PATH.read_text(encoding="utf-8"))
L = len(DECK)
if L < 1:
    raise RuntimeError("oracle.json jest pusty — dodaj wpisy.")

# ---- aplikacja ----
app = FastAPI(title="Wyrocznia kwantowa")

def day_key() -> str:
    # jedna permutacja na dobę (wg czasu Warszawy)
    return datetime.now(ZoneInfo(APP_TZ)).date().isoformat()

def seed_for_day(key: str) -> int:
    mac = hmac.new(SECRET_SALT.encode("utf-8"), key.encode("utf-8"), hashlib.sha256).digest()
    return int.from_bytes(mac[:8], "big", signed=False)  # 64-bit seed

def permute_indices(seed: int, n: int) -> list[int]:
    idx = list(range(n))
    rng = random.Random(seed)  # deterministyczny dla danego seeda
    rng.shuffle(idx)
    return idx

@app.get("/health")
def health():
    return {"status": "ok", "date": day_key(), "cards": L, "tz": APP_TZ}

@app.get("/oracle")
def oracle(n: int = Query(..., ge=1, le=10_000_000)):
    key = day_key()
    perm = permute_indices(seed_for_day(key), L)
    idx = (n - 1) % L
    entry = DECK[perm[idx]]
    return JSONResponse({"date": key, "input_number": n, "result": entry["text"]})
@app.get("/", response_class=HTMLResponse)
def index():
    max_n = L  # X
    return f"""<!doctype html>
<html lang="pl">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wyrocznia</title>
<style>
  :root {{
    --bg:#070b17; --ink:#e6e9f4; --muted:#9aa4c7;
    --glass: rgba(255,255,255,.06); --edge: rgba(255,255,255,.14);
  }}
  html,body {{ height:100%; margin:0; background: radial-gradient(60vw 60vh at 50% 10%, #101a36 0%, transparent 60%), radial-gradient(40vw 50vh at 80% 90%, #0f1b35 0%, transparent 60%), var(--bg); color:var(--ink); }}
  body {{ display:grid; place-items:center; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, "Helvetica Neue", Arial, sans-serif; }}
  .wrap {{ width:min(800px, 92vw); }}
  .panel {{ padding:2.2rem 1.6rem; border:1px solid var(--edge); border-radius:22px; background:var(--glass); backdrop-filter: blur(8px); box-shadow: 0 30px 80px rgba(0,0,0,.45), inset 0 0 120px rgba(140,200,255,.08); }}
  .prompt {{ text-align:center; font-size:clamp(1.1rem, 2.6vw, 1.6rem); letter-spacing:.02em; margin:0 0 1.1rem 0; }}
  form {{ display:flex; gap:.6rem; justify-content:center; }}
  input[type=number] {{ width:220px; padding:.8rem 1rem; font-size:1.05rem; border-radius:12px; border:1px solid var(--edge); background:rgba(255,255,255,.08); color:var(--ink); outline:none; text-align:center; }}
  button {{ padding:.8rem 1.1rem; font-size:1.05rem; border-radius:12px; border:1px solid var(--edge); background:linear-gradient(180deg, rgba(255,255,255,.12), rgba(255,255,255,.06)); color:var(--ink); cursor:pointer; }}
  button:hover {{ box-shadow:0 0 22px rgba(140,200,255,.25); }}
  .card {{ margin-top:1.2rem; border:1px solid var(--edge); border-radius:18px; padding:1.2rem 1.2rem; min-height:3.6rem; background:rgba(255,255,255,.05); }}
  .oracle {{ font-family: ui-serif, Georgia, "Times New Roman", serif; font-size:clamp(1.15rem, 2.4vw, 1.6rem); line-height:1.5; }}
  .err {{ color:#ffb4b4; }}
  /* dyskretna „pieczęć” */
  .sigil {{ position:fixed; inset:auto -120px -120px auto; width:360px; height:360px; opacity:.18; filter: blur(0.3px); }}
</style>

<div class="wrap">
  <div class="panel">
    <p class="prompt">Wybierz liczbę od <strong>1</strong> do <strong>{max_n}</strong></p>
    <form id="f" autocomplete="off">
      <input id="n" type="number" min="1" max="{max_n}" step="1" placeholder="1–{max_n}" required>
      <button type="submit">Odsłoń</button>
    </form>
    <div id="out" class="card"><div id="txt" class="oracle"></div></div>
  </div>
</div>

<svg class="sigil" viewBox="0 0 100 100" aria-hidden="true">
  <defs><radialGradient id="g" cx="50%" cy="50%" r="60%"><stop offset="0%" stop-color="#8ad1ff"/><stop offset="100%" stop-color="transparent"/></radialGradient></defs>
  <circle cx="50" cy="50" r="48" fill="none" stroke="url(#g)" stroke-width="0.6"/>
  <circle cx="50" cy="50" r="36" fill="none" stroke="url(#g)" stroke-width="0.5"/>
  <path d="M50 6 L62 32 L94 36 L70 56 L76 86 L50 72 L24 86 L30 56 L6 36 L38 32 Z" fill="none" stroke="url(#g)" stroke-width="0.5"/>
</svg>

<script>
  const f = document.getElementById('f');
  const n = document.getElementById('n');
  const txt = document.getElementById('txt');
  const MAX = {max_n};
  f.addEventListener('submit', async (e) => {{
    e.preventDefault();
    const num = parseInt(n.value, 10);
    if (!Number.isInteger(num) || num < 1 || num > MAX) {{
      txt.innerHTML = '<span class="err">Podaj liczbę 1–' + MAX + '.</span>';
      return;
    }}
    txt.textContent = '…';
    try {{
      const r = await fetch('/oracle?n=' + encodeURIComponent(num));
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const data = await r.json();
      txt.textContent = data.result || '—';
    }} catch (err) {{
      txt.innerHTML = '<span class="err">Błąd połączenia.</span>';
    }}
  }});
</script>
</html>
"""
