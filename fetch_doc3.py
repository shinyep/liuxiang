import urllib.request, json, sys

sys.stdout.reconfigure(encoding="utf-8")

# Try the doc API endpoints
endpoints = [
    "https://agnes-ai.com/api/doc/agnes-video-v20",
    "https://agnes-ai.com/api/docs?identifier=agnes-video-v20",
    "https://agnes-ai.com/api/docs/agnes-video-v20",
]

for ep in endpoints:
    try:
        req = urllib.request.Request(ep, headers={"Accept": "application/json"})
        r = urllib.request.urlopen(req, timeout=15)
        data = r.read().decode("utf-8", "replace")
        print(f"\n=== {ep} ({len(data)} chars) ===")
        print(data[:5000])
        if len(data) > 5000:
            print("... (truncated)")
    except Exception as e:
        print(f"\n{ep}: {e}")
