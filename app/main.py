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
    font-size: 2.4rem;
    margin:0 0 2rem 0;
    letter-spacing:.04em;
    text-shadow:0 0 12px rgba(180,220,255,.5);
  }}
  .oracle-box {{
    width:min(480px, 100%);
    background: rgba(255,255,255,.05);
    border:1px solid rgba(255,255,255,.15);
    border-radius:20px;
    padding:1.6rem;
    box-shadow:0 20px 50px rgba(0,0,0,.4);
    text-align:center;
  }}
  .oracle-title {{
    font-size:1.2rem;
    margin:0 0 1.2rem 0;
    color:#dbe6ff;
  }}
  form {{
    display:flex; gap:.6rem; justify-content:center; flex-wrap:wrap;
    margin-bottom:1rem;
  }}
  input[type=number] {{
    padding:.7rem 1rem;
    border-radius:10px;
    border:1px solid rgba(255,255,255,.2);
    background:rgba(255,255,255,.08);
    color:#f0f2fa;
    font-size:1rem;
    width:200px; text-align:center;
  }}
  button {{
    padding:.7rem 1rem;
    border-radius:10px;
    border:1px solid rgba(255,255,255,.2);
    background:linear-gradient(180deg, rgba(255,255,255,.12), rgba(255,255,255,.06));
    color:#f0f2fa; font-size:1rem; cursor:pointer;
  }}
  button:hover {{ box-shadow:0 0 14px rgba(160,200,255,.3); }}
  .answer {{
    min-height:3rem;
    padding:1rem;
    border-radius:12px;
    border:1px solid rgba(255,255,255,.15);
    background:rgba(255,255,255,.03);
    font-size:1.05rem;
    line-height:1.4;
  }}
</style>

<h1>Wyrocznia Kwantowa</h1>

<div class="oracle-box">
  <div class="oracle-title">Co mnie czeka w najbliższym czasie</div>
  <form id="f" autocomplete="off">
    <input id="n" type="number" min="1" max="{max_n}" step="1" placeholder="Wybierz liczbę od 1 do {max_n}" required>
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
    const num = parseInt(n.value, 10);
    if (!Number.isInteger(num) || num < 1 || num > MAX) {{
      out.textContent = 'Podaj liczbę z zakresu 1–' + MAX;
      return;
    }}
    out.textContent = '...';
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
