#!/usr/bin/env python3
import os
import requests

AUTH_TOKEN = os.getenv("SPIN_AUTH_TOKEN")
DEVICE_ID = os.getenv("SPIN_DEVICE_ID")

if not AUTH_TOKEN or not DEVICE_ID:
    raise SystemExit("Missing required environment variables: SPIN_AUTH_TOKEN and SPIN_DEVICE_ID")

URL = "https://spinpk.net/api/spin.php"
HEADERS = {
    "sec-ch-ua-platform": '"Android"',
    "authorization": f"Bearer {AUTH_TOKEN}",
    "x-device-id": DEVICE_ID,
    "user-agent": "Mozilla/5.0 (Linux; Android 11; Infinix X659B Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/152.0.7977.30 Mobile Safari/537.36",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Android WebView";v="152"',
    "content-type": "application/json",
    "sec-ch-ua-mobile": "?1",
    "accept": "/",
    "origin": "null",
    "x-requested-with": "com.spinpk.app",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "accept-encoding": "gzip, deflate, zstd",
    "accept-language": "en-US,en;q=0.9",
    "priority": "u=1, i",
}
PAYLOAD = {"action": "play"}


def main():
    try:
        resp = requests.post(URL, headers=HEADERS, json=PAYLOAD, timeout=30)
        print("Status:", resp.status_code)
        print(resp.text)
    except Exception as e:
        print("Request failed:", e)


if __name__ == "__main__":
    main()
