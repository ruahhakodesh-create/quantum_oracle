from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import json
from pathlib import Path
import hmac, hashlib, random, os
from datetime import datetime
from zoneinfo import ZoneInfo

# konfiguracja
APP_TZ = os.getenv("APP_TZ", "Europe/Warsaw")
SECRET_SALT = os.getenv("SECRET_SALT", "domyslny_klucz")  # awaryjnie
DECK = json.loads(Path(__file__).with_name("oracle.json").read_text(encoding="utf-8"))
L = len(DECK)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "cards": L}

def day_key() -> str:
    d = datetime.now(ZoneInfo(APP_TZ)).date()
    return d.isoformat()

def seed_for_day(key: str) -> int:
    mac = hmac.new(SECRET_SALT.encode("utf-8"), key.encode("utf-8"), hashlib.sha256).digest()
    return int.from_bytes(mac[:8], "big")

def permute_indices(seed: int, n: int) -> list[int]:
    idx = list(range(n))
    rng = random.Random(seed)
    rng.shuffle(idx)
    return idx

@app.get("/oracle")
def oracle(n: int = Query(..., ge=1, le=10000)):
    key = day_key()
    seed = seed_for_day(key)
    perm = permute_indices(seed, L)
    idx = (n - 1) % L
    entry = DECK[perm[idx]]
    return JSONResponse({
        "date": key,
        "input_number": n,
        "result": entry["text"]
    })
    from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html lang="pl">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wyrocznia kwantowa</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial,sans-serif;max-width:700px;margin:4rem auto;padding:0 1rem;line-height:1.5}
  h1{font-size:1.6rem;margin:0 0 1rem}
  form{display:flex;gap:.5rem;margin-bottom:1rem}
  input[type=number]{flex:1;padding:.6rem .8rem;font-size:1rem}
  button{padding:.6rem 1rem;font-size:1rem;cursor:pointer}
  #out{margin-top:1rem;padding:1rem;border:1px solid #ddd;border-radius:8px;min-height:3rem}
  small{color:#666}
</style>
<h1>Wyrocznia kwantowa</h1>
<form id="f">
  <input id="n" type="number" min="1" step="1" placeholder="Wpisz liczbę" required>
  <button type="submit">Sprawdź</button>
</form>
<small>Nowe przyporządkowanie liczb co dobę.</small>
<div id="out"></div>
<script>
  const f = document.getElementById('f');
  const n = document.getElementById('n');
  const out = document.getElementById('out');
  f.addEventListener('submit', async (e) => {
    e.preventDefault();
    out.textContent = '...';
    const num = parseInt(n.value, 10);
    const r = await fetch('/oracle?n=' + encodeURIComponent(num));
    if (!r.ok) { out.textContent = 'Błąd: ' + r.status; return; }
    const data = await r.json();
    out.textContent = data.result || 'Brak odpowiedzi';
  });
</script>
</html>
"""

