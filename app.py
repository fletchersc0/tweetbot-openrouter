from flask import Flask, jsonify, send_from_directory
import requests, string, os, json, time, math, pathlib

app = Flask(__name__)

# ---------- CONFIG ---------- #
EPOCH = 1753189200 # 22/07/2025
CACHE_FILE = pathlib.Path("cache.json")
CHARS = [' '] + list(string.ascii_uppercase)
BASE = len(CHARS)
MAX_LENGTH = 280
MODEL = "mistralai/mistral-7b-instruct"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---------- HELPERS ---------- #
def number_to_string(n: int) -> str:
    s = ""
    while n:
        n, rem = divmod(n, BASE)
        s = CHARS[rem] + s
    return s[:MAX_LENGTH] or "A"  # never empty

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    return {}

def save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache))

def call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "[ERROR] OPENROUTER_API_KEY not set."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=25,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"[ERROR] {exc}"

# ---------- ROUTES ---------- #
@app.route("/api/current")
def api_current():
    """Return today’s hour‑indexed tweet + LLM reply."""
    cache = load_cache()

    # work out hour index since epoch
    hours_since = math.floor((time.time() - EPOCH) / 3600)
    n = hours_since + 1

    if str(n) not in cache:
        prompt = number_to_string(n)
        reply = call_openrouter(prompt)
        cache[str(n)] = {"prompt": prompt, "reply": reply}
        save_cache(cache)

    # seconds until next hour
    secs_left = 3600 - int(time.time() % 3600)

    return jsonify(
        index=n,
        prompt=cache[str(n)]["prompt"],
        reply=cache[str(n)]["reply"],
        seconds_until_next=secs_left,
    )

@app.route("/")
def index():
    # serve static HTML file
    return send_from_directory("static", "index.html")

# ---------- ENTRY ---------- #
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
