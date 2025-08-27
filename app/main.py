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
    return f"""<!doctype html>
<html lang="pl">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wyrocznia Kwantowa</title>
<style>
  body {{
    margin:0; padding:0;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial, sans-serif;
    background: linear-gradient(180deg, #0a0f24, #141a33);
    color: #f0f2fa;
    display:flex; flex-direction:column; align-items:center;
    min-height:100vh; justify-content:flex-start; padding:3rem 1rem;
  }}
  h1 {{
    font-family: ui-serif, Georgia, "Times New Roman", serif;  /* miększy krój */
    font-weight: 600;
    font-size: clamp(2.2rem, 5vw, 3rem);
    margin:0 0 2.2rem 0;
    letter-spacing:.01em;
    text-shadow:0 0 14px rgba(180,220,255,.45);
  }}
  .oracle-box {{
    width:min(560px, 100%);
    background: rgba(255,255,255,.05);
    border:1px solid rgba(255,255,255,.15);
    border-radius:22px;
    padding:1.6rem;
    box-shadow:0 20px 50px rgba(0,0,0,.4);
    text-align:center;
  }}
  .oracle-title {{
    font-size:1.2rem;
    margin:0 0 1.2rem 0;
    color:#dbe6ff;
    font-family: ui-serif, Georgia, "Times New Roman", serif;
  }}
  form {{
    display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap;
    margin-bottom:1rem;
  }}
  /* Szersze pole + brak spinnerów */
  .num-input {{
    width:min(360px, 90%);
    padding:.8rem 1rem;
    border-radius:12px;
    border:1px solid rgba(255,255,255,.2);
    background:rgba(255,255,255,.08);
    color:#f0f2fa;
    font-size:1.05rem;
    text-align:center;
    outline:none;
  }}
  /* ukrycie spinnerów, gdyby przeglądarka mimo wszystko je dodała */
  input::-webkit-outer-spin-button,
  input::-webkit-inner-spin-button {{ -webkit-appearance: none; margin: 0; }}
  input[type=number] {{ -moz-appearance: textfield; }}

  button {{
    padding:.8rem 1.1rem;
    border-radius:12px;
    border:1px solid rgba(255,255,255,.2);
    background:linear-gradient(180deg, rgba(255,255,255,.12), rgba(255,255,255,.06));
    color:#f0f2fa; font-size:1.05rem; cursor:pointer;
  }}
  button:hover {{ box-shadow:0 0 14px rgba(160,200,255,.3); }}
  .answer {{
    min-height:3.2rem;
    padding:1rem;
    border-radius:14px;
    border:1px solid rgba(255,255,255,.15);
    background:rgba(255,255,255,.03);
    font-size:1.08rem;
    line-height:1.45;
  }}
  .err {{ color:#ffb4b4; }}
</style>

<h1>Wyrocznia Kwantowa</h1>

<div class="oracle-box">
  <div class="oracle-title">Co mnie czeka w najbliższym czasie</div>
  <form id="f" autocomplete="off">
    <input id="n" class="num-input" type="text" inputmode="numeric" pattern="[0-9]*"
           placeholder="wybierz od 1 do {max_n}" aria-label="wybierz od 1 do {max_n}" required>
    <button type="submit">Odsłoń</button>
  </form>
  <div id="out" class="answer"></div>
</div>

<script>
  const f = document.getElementById('f');
  const n = document.getElementById('n');
  const out = document.getElementById('out');
  const MAX = {max_n};

  f.addEventListener('submit', async (e) => {{
    e.preventDefault();
    const raw = (n.value || '').trim();
    const num = Number(raw);
    if (!/^[0-9]+$/.test(raw) || !Number.isInteger(num) || num < 1 || num > MAX) {{
      out.innerHTML = '<span class="err">Podaj liczbę 1–' + MAX + '.</span>';
      return;
    }}
    out.textContent = '…';
    try {{
      const r = await fetch('/oracle?n=' + encodeURIComponent(num));
      const data = await r.json();
      out.textContent = data.result || '—';
    }} catch (err) {{
      out.textContent = 'Błąd połączenia.';
    }}
  }});
</script>
</html>
"""
