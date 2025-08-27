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
    max_n = L
    today = day_key()
    return f"""<!doctype html>
<html lang="pl">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wyrocznia kwantowa</title>
<style>
  :root {{
    --bg1:#0b1020; --bg2:#0d1b2a; --glow:rgba(120,190,255,.55);
    --card:rgba(255,255,255,.06); --card-b:rgba(255,255,255,.12);
    --txt:#eef3ff; --muted:#9fb3d9;
  }}
  html,body {{height:100%;margin:0}}
  body {{
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, "Helvetica Neue", Arial, sans-serif;
    color: var(--txt);
    background:
      radial-gradient(1200px 800px at 20% 10%, #122043 0%, transparent 60%),
      radial-gradient(800px 600px at 80% 90%, #1a2748 0%, transparent 60%),
      linear-gradient(180deg, var(--bg1), var(--bg2));
    display:flex; align-items:center; justify-content:center; padding:2rem;
  }}
  .wrap {{ width:min(720px,100%); text-align:center; }}
  .title {{ font-size:clamp(1.6rem,2.6vw,2.2rem); margin:0 0 .3rem; text-shadow:0 0 18px var(--glow); }}
  .sub {{ color:var(--muted); margin:0 0 1.2rem; font-size:.98rem; }}
  .panel {{
    background:var(--card); border:1px solid var(--card-b); border-radius:16px;
    backdrop-filter:blur(6px); padding:1rem; box-shadow:0 10px 40px rgba(0,0,0,.35), 0 0 60px 0 var(--glow) inset;
  }}
  form {{ display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap; margin:.25rem 0 1rem; }}
  input[type=number] {{
    width:220px; padding:.7rem .9rem; font-size:1rem; border-radius:10px; border:1px solid var(--card-b);
    background:rgba(255,255,255,.08); color:var(--txt); outline:none;
  }}
  button {{
    padding:.7rem 1rem; font-size:1rem; border-radius:10px; cursor:pointer; border:1px solid var(--card-b);
    background:linear-gradient(180deg, rgba(255,255,255,.10), rgba(255,255,255,.06)); color:var(--txt);
    transition:transform .08s ease, box-shadow .2s ease;
  }}
  button:hover {{ transform:translateY(-1px); box-shadow:0 0 18px var(--glow); }}
  .hint {{ color:var(--muted); font-size:.9rem; margin:.3rem 0 .6rem; }}
  .card {{
    margin-top:.6rem; text-align:left; border:1px solid var(--card-b); border-radius:14px;
    padding:1rem .95rem; background:rgba(255,255,255,.05); box-shadow:0 0 24px rgba(139,233,253,.15);
    min-height:3.2rem;
  }}
  .meta {{ color:var(--muted); font-size:.85rem; margin-top:.4rem; }}
  .err {{ color:#ffb4b4; }}
</style>

<div class="wrap">
  <h1 class="title">Wyrocznia kwantowa</h1>
  <p class="sub">Dzisiejsze przyporządkowanie: <strong>{today}</strong>. Wpisz liczbę z zakresu <strong>1–{max_n}</strong>.</p>

  <div class="panel">
    <form id="f">
      <input id="n" type="number" min="1" max="{max_n}" step="1" placeholder="Wpisz liczbę 1–{max_n}" required>
      <button type="submit">Odsłoń</button>
    </form>
    <div class="hint">Jedna odpowiedź na dziś. Jutro układ będzie inny.</div>
    <div id="out" class="card"></div>
    <div id="meta" class="meta"></div>
  </div>
</div>

<script>
  const f = document.getElementById('f');
  const n = document.getElementById('n');
  const out = document.getElementById('out');
  const meta = document.getElementById('meta');
  const MAX = {max_n};

  f.addEventListener('submit', async (e) => {{
    e.preventDefault();
    const num = parseInt(n.value, 10);
    if (!Number.isInteger(num) || num < 1 || num > MAX) {{
      out.innerHTML = '<span class="err">Podaj liczbę z zakresu 1–' + MAX + '.</span>';
      meta.textContent = '';
      return;
    }}
    out.textContent = '...';
    meta.textContent = '';
    try {{
      const r = await fetch('/oracle?n=' + encodeURIComponent(num));
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const data = await r.json();
      out.textContent = data.result || 'Brak odpowiedzi';
      meta.textContent = 'Liczba: ' + num + ' • Data: ' + (data.date || '{today}');
    }} catch (err) {{
      out.innerHTML = '<span class="err">Błąd połączenia. Spróbuj ponownie.</span>';
      console.error(err);
    }}
  }});
</script>
</html>
"""
