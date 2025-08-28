# app/main.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json, os, hmac, hashlib, random

# ---- konfiguracja ----
APP_TZ = os.getenv("APP_TZ", "Europe/Warsaw")
SECRET_SALT = os.getenv("SECRET_SALT", "domyslny_klucz")

# ---- wczytanie talii ----
DECK_PATH = Path(__file__).with_name("oracle.json")
DECK = json.loads(DECK_PATH.read_text(encoding="utf-8"))
L = len(DECK)
if L < 1:
    raise RuntimeError("oracle.json jest pusty — dodaj wpisy.")

# ---- aplikacja ----
app = FastAPI(title="Wyrocznia kwantowa")
# montowanie plików statycznych (np. tło)
app.mount("/static", StaticFiles(directory=str(Path(__file__).with_name("static"))), name="static")

def day_key() -> str:
    return datetime.now(ZoneInfo(APP_TZ)).date().isoformat()

def seed_for_day(key: str) -> int:
    mac = hmac.new(SECRET_SALT.encode("utf-8"), key.encode("utf-8"), hashlib.sha256).digest()
    return int.from_bytes(mac[:8], "big", signed=False)

def permute_indices(seed: int, n: int) -> list[int]:
    idx = list(range(n))
    rng = random.Random(seed)
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
    font-family: ui-serif, Georgia, "Times New Roman", serif;
    color:#eef2ff;
    display:flex; flex-direction:column; align-items:center; justify-content:flex-start;
    min-height:100vh; padding:3.2rem 1rem;
    background: url('/static/bg.png') no-repeat center center fixed;
    background-size: cover;
  }}
  h1 {{
    font-weight:600;
    font-size: clamp(2.4rem, 5.2vw, 3.2rem);
    margin:0 0 3.2rem 0;
    letter-spacing:.01em;
    text-shadow: 0 0 18px rgba(170,210,255,.35);
  }}
  /* ramka: perłowe szkło */
  .oracle-box {{
    width:min(560px, 92vw);
    padding:1.8rem 1.6rem;
    border-radius:24px;
    background: rgba(245,245,255,0.22); /* mleczny efekt */
    backdrop-filter: blur(12px) saturate(120%);
    -webkit-backdrop-filter: blur(12px) saturate(120%);
    border:1px solid rgba(255,255,255,.35);
    box-shadow:
      0 20px 60px rgba(0,0,0,.45),
      inset 0 0 120px rgba(200,220,255,.12);
    text-align:center;
  }}
  .oracle-title {{
    font-size:1.2rem; margin:0 0 1.1rem 0; color:#fefeff;
  }}
  form {{ display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap; margin:0 0 1rem 0; }}
  .num-input {
    width:min(280px, 85%);
    padding:.8rem 1rem;
    border-radius:14px;
    border:1px solid rgba(255,255,255,.35);
    background: rgba(255,255,255,.92);   /* perłowe pole */
    color:#1a1c24;                       /* ciemniejszy tekst */
    font-size:1.05rem;
    text-align:center;
    outline:none;
    box-shadow:
      0 4px 12px rgba(0,0,0,.25),        /* cień w dół */
      0 0 16px rgba(180,220,255,.35);    /* delikatny glow */
    transition: box-shadow .15s ease, transform .06s ease;
}
.num-input:focus {
    box-shadow:
      0 6px 16px rgba(0,0,0,.3),
      0 0 22px rgba(180,220,255,.5);     /* mocniejszy glow przy fokusie */
    transform: translateY(-1px);
}

  input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {{ -webkit-appearance:none; margin:0; }}
  input[type=number] {{ -moz-appearance:textfield; }}
  button {{
    padding:.8rem 1.1rem; border-radius:14px; cursor:pointer;
    border:1px solid rgba(255,255,255,.35);
    background: linear-gradient(180deg, rgba(255,255,255,.3), rgba(255,255,255,.15));
    color:#fefeff; font-size:1.05rem;
    transition: box-shadow .15s ease, transform .06s ease;
  }}
  button:hover {{ box-shadow:0 0 18px rgba(160,210,255,.4); transform: translateY(-1px); }}
  .answer {{
    min-height:3.2rem;
    padding:1rem 1.1rem;
    border-radius:16px;
    border:1px solid rgba(255,255,255,.35);
    background: rgba(245,245,255,0.2);
    box-shadow: inset 0 0 40px rgba(200,220,255,.1);
    font-size:1.08rem; line-height:1.46; text-align:left;
    color:#fefeff;
  }}
  .err {{ color:#ffb8c0; }}
</style>

<h1>Wyrocznia Kwantowa</h1>

<div class="oracle-box">
  <div class="oracle-title">Co mnie czeka w najbliższym czasie</div>
  <form id="f" autocomplete="off">
    <input id="n" class="num-input" type="text" inputmode="numeric" pattern="[0-9]*"
           placeholder="wpisz liczbę od 1 do {max_n}" aria-label="wpisz liczbę od 1 do {max_n}" required>
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
    }} catch {{ out.textContent = 'Błąd połączenia.'; }}
  }});
</script>
</html>
"""
