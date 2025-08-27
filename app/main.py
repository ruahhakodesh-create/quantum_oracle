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
