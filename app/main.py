# app/main.py
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os, json, hmac, hashlib, random

# ----------------- konfiguracja -----------------
APP_TZ = os.getenv("APP_TZ", "Europe/Warsaw")
SECRET_SALT = os.getenv("SECRET_SALT", "domyslny_klucz")  # USTAW to w Render → Environment

# ----------------- dane -----------------
DECK_PATH = Path(__file__).with_name("oracle.json")
DECK = json.loads(DECK_PATH.read_text(encoding="utf-8"))
L = len(DECK)
if L < 1:
    raise RuntimeError("oracle.json jest pusty — dodaj wpisy.")

# ----------------- aplikacja -----------------
app = FastAPI(title="Wyrocznia Kwantowa")
app.mount("/static", StaticFiles(directory=str(Path(__file__).with_name("static"))), name="static")

def day_key() -> str:
    """Klucz dnia w lokalnej strefie (np. 2025-08-29)."""
    return datetime.now(ZoneInfo(APP_TZ)).date().isoformat()

def seed_for_day(key: str) -> int:
    """Deterministyczny seed z (data + SECRET_SALT)."""
    mac = hmac.new(SECRET_SALT.encode("utf-8"), key.encode("utf-8"), hashlib.sha256).digest()
    return int.from_bytes(mac[:8], "big", signed=False)

def permute_indices(seed: int, n: int) -> list[int]:
    """Permutation shuffle zależny od seeda."""
    idx = list(range(n))
    rnd = random.Random(seed)
    rnd.shuffle(idx)
    return idx

@app.get("/health")
def health():
    return {"status": "ok", "date": day_key(), "cards": L, "tz": APP_TZ}

@app.get("/oracle")
def oracle(n: int = Query(..., ge=1, le=10_000_000)):
    """
    Zwraca sentencję z dziennej permutacji:
    - tworzę permutację [0..L-1] deterministycznie dla (data, SECRET_SALT),
    - mapuję podaną liczbę n na indeks (n-1) % L,
    - zwracam DECK[perm[idx]].
    """
    key = day_key()
    perm = permute_indices(seed_for_day(key), L)
    idx = (n - 1) % L
    entry = DECK[perm[idx]]
    return JSONResponse({"date": key, "input_number": n, "result": entry["text"]})

# ----------------- UI -----------------
@app.get("/", response_class=HTMLResponse)
def index():
    max_n = L
    return f"""<!doctype html>
<html lang="pl" translate="no" class="notranslate">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google" content="notranslate">
<title>Wyrocznia Kwantowa</title>
<style>
  :root {{
    --ink:#eef2ff; --ink-dark:#10121a; --cream:#e8e0d0;
    --glass: rgba(245,245,255,0.22);
    --glass-strong: rgba(245,245,255,0.28);
    --stroke: rgba(255,255,255,.38);
    --halo: rgba(170,210,255,.35);
  }}
  html,body {{ height:100%; margin:0; }}
  body {{
    font-family: ui-serif, Georgia, "Times New Roman", serif;
    color: var(--ink);
    display:flex; flex-direction:column; align-items:center; justify-content:flex-start;
    min-height:100vh; padding:3.2rem 1rem;
    background: url('/static/bg.png') no-repeat center center fixed;
    background-size: cover;
  }}
  h1 {{
    font-weight:600;
    font-size: clamp(2.4rem, 5.2vw, 3.2rem);
    letter-spacing:.01em;
    margin:0 0 0.6rem 0;
    text-shadow: 0 0 18px rgba(170,210,255,.35);
  }}
  .subtitle {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: clamp(1.2rem, 2.6vw, 1.45rem);
    margin: 0 0 2.6rem 0;
    color: var(--cream);
    text-shadow: 0 0 6px rgba(0,0,0,.5);
  }}

  /* ——— ramka „magiczna” ——— */
  @keyframes pulseHalo {{
    0%   {{ box-shadow: 0 24px 60px rgba(0,0,0,.42), 0 0 0 0 rgba(160,210,255,.0); }}
    50%  {{ box-shadow: 0 24px 60px rgba(0,0,0,.46), 0 0 32px 6px rgba(160,210,255,.12); }}
    100% {{ box-shadow: 0 24px 60px rgba(0,0,0,.42), 0 0 0 0 rgba(160,210,255,.0); }}
  }}

  .oracle-box {{
    position: relative;
    width:min(560px, 92vw);
    padding:2rem 1.6rem;
    border-radius:26px;
    background: var(--glass);
    backdrop-filter: blur(14px) saturate(120%);
    -webkit-backdrop-filter: blur(14px) saturate(120%);
    border:1px solid var(--stroke);
    box-shadow: 0 24px 60px rgba(0,0,0,.45), inset 0 0 120px rgba(200,220,255,.10);
    text-align:center;
    animation: pulseHalo 6s ease-in-out infinite;
  }}
  /* gradientowy border w pseudoelemencie */
  .oracle-box::before {{
    content:"";
    position:absolute; inset:0; border-radius:26px; pointer-events:none;
    padding:1px;
    background: linear-gradient(135deg, rgba(160,210,255,.55), rgba(255,255,255,.15));
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude;
  }}
  /* lekka poświata na krawędziach */
  .oracle-box::after {{
    content:"";
    position:absolute; inset:-4px; border-radius:30px; pointer-events:none;
    box-shadow: 0 0 40px rgba(160,210,255,.25);
  }}

  .oracle-title {{
    font-size:1.2rem; margin:0 0 1.1rem 0; color:#fefeff;
    letter-spacing:.02em;
  }}

  form {{ display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap; margin:0 0 1rem 0; }}
  .num-input {{
    width: min(280px, 85%);
    padding: .8rem 1rem;
    border-radius: 14px;
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,.92);
    color: var(--ink-dark);
    font-size: 1.05rem;
    text-align: center;
    outline: none;
    box-shadow: 0 4px 12px rgba(0,0,0,.25), 0 0 16px rgba(180,220,255,.35);
    transition: box-shadow .15s ease, transform .06s ease, opacity .15s ease;
  }}
  input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {{ -webkit-appearance: none; margin: 0; }}
  input[type=number] {{ -moz-appearance: textfield; }}
  .num-input:focus {{
    box-shadow: 0 6px 16px rgba(0,0,0,.3), 0 0 24px rgba(180,220,255,.55);
    transform: translateY(-1px);
  }}
  .btn {{
    padding:.8rem 1.1rem; border-radius:14px; cursor:pointer;
    border:1px solid var(--stroke);
    background: linear-gradient(180deg, rgba(255,255,255,.30), rgba(255,255,255,.14));
    color:#fefeff; font-size:1.05rem;
    transition: box-shadow .15s ease, transform .06s ease, opacity .15s ease;
  }}
  .btn:hover {{ box-shadow:0 0 18px rgba(160,210,255,.4); transform: translateY(-1px); }}
  .btn-secondary {{
    display:none;
    margin-top:.8rem;
    background: linear-gradient(180deg, rgba(255,255,255,.22), rgba(255,255,255,.12));
  }}
  .answer {{
    min-height:3.2rem;
    padding:1rem 1.1rem;
    border-radius:16px;
    border:1px solid var(--stroke);
    background: rgba(245,245,255,0.20);
    box-shadow: inset 0 0 40px rgba(200,220,255,.10);
    font-size:1.08rem; line-height:1.46; text-align:left;
    color:#fefeff;
  }}
  .err {{ color:#ffb8c0; }}
  .disabled {{ opacity:.55; pointer-events:none; }}
</style>

<h1>Wyrocznia Kwantowa</h1>
<p class="subtitle">Skup się i wybierz liczbę od 1 do {max_n}</p>

<div class="oracle-box">
  <div class="oracle-title">Co mnie czeka w najbliższym czasie</div>
  <form id="f" autocomplete="off">
    <input id="n" class="num-input" type="text" inputmode="numeric" pattern="[0-9]*"
           placeholder="wybierz od 1 do {max_n}" aria-label="wybierz od 1 do {max_n}" required>
    <button id="go" class="btn" type="submit">Odsłoń</button>
  </form>
  <div id="out" class="answer"></div>
  <button id="reset" class="btn btn-secondary" type="button">Wróć</button>
</div>

<script>
  const f = document.getElementById('f');
  const n = document.getElementById('n');
  const out = document.getElementById('out');
  const go = document.getElementById('go');
  const resetBtn = document.getElementById('reset');
  const MAX = {max_n};
  let locked = false;

  function lockUI() {{
    locked = true;
    n.classList.add('disabled');
    go.classList.add('disabled');
    n.setAttribute('disabled','disabled');
    go.setAttribute('disabled','disabled');
    resetBtn.style.display = 'inline-block';
  }}

  function typeText(el, text, delay=20) {{
    el.textContent = '';
    let i = 0;
    function step() {{
      if (i < text.length) {{
        el.textContent += text[i++];
        setTimeout(step, delay);
      }}
    }}
    step();
  }}

  f.addEventListener('submit', async (e) => {{
    e.preventDefault();
    if (locked) return;

    const raw = (n.value || '').trim();
    const num = Number(raw);
    if (!/^[0-9]+$/.test(raw) || !Number.isInteger(num) || num < 1 || num > MAX) {{
      out.innerHTML = '<span class="err">Podaj liczbę 1–' + MAX + '.</span>';
      return;
    }}

    out.textContent = '…';
    go.classList.add('disabled');
    try {{
      const r = await fetch('/oracle?n=' + encodeURIComponent(num));
      const data = await r.json();
      const text = (data && data.result) ? data.result : '—';
      typeText(out, text, 20);
      lockUI();
    }} catch {{
      out.textContent = 'Błąd połączenia.';
      go.classList.remove('disabled');
    }}
  }});

  resetBtn.addEventListener('click', () => {{
    location.reload();
  }});
</script>
</html>
"""
