import urllib.request, re, sys

sys.stdout.reconfigure(encoding="utf-8")

# Let's look at all chunks for any API URL
chunks = [
    "115-42068af32f464999.js",
    "412-3bc7c9e844b7244b.js",
    "124-8cc4f6a801808237.js",
    "548-96a745c871a21877.js",
    "503-120661aef68d9bdb.js",
    "63-a480889af740aff1.js",
    "972-a0a4ec8df69c5aee.js",
    "797-76d65886b211eb8f.js",
    "494-9df5b0175ed041af.js",
    "177-44c32b22bdd64ace.js",
]

for chunk in chunks:
    try:
        url = f"https://agnes-ai.com/_next/static/chunks/{chunk}"
        r = urllib.request.urlopen(url, timeout=10)
        data = r.read().decode("utf-8", "replace")
        # Search for agnes-ai.com API URLs
        matches = re.findall(r'agnes-ai\.com[^"\'`\s]{3,100}', data)
        if matches:
            print(f"\n=== {chunk} ({len(data)} chars) ===")
            for m in set(matches):
                print(f"  {m}")
        # Also look for /api/ paths
        api_matches = re.findall(r'"/api/[^"]*"', data)
        if api_matches:
            print(f"  API paths: {set(api_matches)}")
    except Exception as e:
        print(f"{chunk}: error")
