from flask import Flask, request, jsonify
import requests
import string
import os

app = Flask(__name__)

# 27 characters: space + A-Z
CHARS = [' '] + list(string.ascii_uppercase)
BASE = len(CHARS)
MAX_LENGTH = 280
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def number_to_string(n):
    s = ''
    while n > 0:
        n, rem = divmod(n, BASE)
        s = CHARS[rem] + s
    return s

def call_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",  # optional but polite
    }
    body = {
        "model": "mistralai/mistral-7b-instruct",  # or another free model
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    try:
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "[ERROR] Could not parse response."

@app.route("/", methods=["GET"])
def home():
    return "Tweet Generator LLM API is live."

@app.route("/generate", methods=["POST"])
def generate():
    n = request.json.get("number", 1)
    prompt = number_to_string(n)
    response = call_openrouter(prompt)
    return jsonify({
        "input": prompt,
        "response": response
    })
