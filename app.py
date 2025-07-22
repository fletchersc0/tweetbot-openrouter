from flask import Flask, request, jsonify
import requests
import string
import os

app = Flask(__name__)

# 27‑character alphabet: space + A‑Z
CHARS = [' '] + list(string.ascii_uppercase)
BASE = len(CHARS)
MAX_LENGTH = 280

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # set in Render

# ---------- helpers ----------
def number_to_string(n: int) -> str:
    """Convert positive integer to base‑27 string using CHARS."""
    if n <= 0:
        return ""
    s = ""
    while n:
        n, rem = divmod(n, BASE)
        s = CHARS[rem] + s
    return s[:MAX_LENGTH]  # hard cap at tweet length

def call_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "[ERROR] OPENROUTER_API_KEY not set."
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com"  # polite but optional
    }
    body = {
        "model": "mistralai/mistral-7b-instruct",  # free‑tier model
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=15
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"[ERROR] {exc}"

# ---------- routes ----------
@app.route("/", methods=["GET"])
def home():
    return "Tweet Generator LLM API is live."

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    n = int(data.get("number", 1))
    if n <= 0:
        return jsonify(error="number must be ≥ 1"), 400

    prompt = number_to_string(n)
    response = call_openrouter(prompt)
    return jsonify(input=prompt, response=response)

# ---------- entry ----------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Render injects $PORT
    app.run(host="0.0.0.0", port=port, debug=False)
