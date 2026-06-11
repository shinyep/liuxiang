import urllib.request, re, sys, json

sys.stdout.reconfigure(encoding="utf-8")

# Try to find the doc content API
# Look at the chunk JS files for API endpoints
chunk_url = "https://agnes-ai.com/_next/static/chunks/503-120661aef68d9bdb.js"
r = urllib.request.urlopen(chunk_url, timeout=15)
data = r.read().decode("utf-8", "replace")

# Search for URL patterns with quotes
pattern = r"""(?:["'])((?:https?://|/api/|/doc/)[^"'\s]{5,})(?:["'])"""
urls = re.findall(pattern, data)
for u in set(urls):
    print(f"URL: {u}")

# Also search for "doc" or "content" related function calls
for kw in ["fetch(", "axios", "getDoc", "loadDoc", "docContent", "pageContent"]:
    idx = data.find(kw)
    if idx >= 0:
        print(f"\n--- {kw} at {idx} ---")
        print(data[max(0,idx-30):idx+200])
