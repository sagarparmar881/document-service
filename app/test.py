import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("❌ API key not found in environment")
    exit(1)

url = "https://api.openai.com/v1/chat/completions"

payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "user", "content": "Say hello"}
    ],
    "temperature": 0.2
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

try:
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("✅ API Key Working")
        print("Response:", data["choices"][0]["message"]["content"])

    elif response.status_code == 401:
        print("❌ Invalid API Key (401 Unauthorized)")

    elif response.status_code == 429:
        print("⚠️ Rate limit / quota exceeded (429)")

    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
        print(response.text)

except Exception as e:
    print("❌ Request failed:", str(e))