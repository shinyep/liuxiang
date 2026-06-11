import json, sys

sys.stdout.reconfigure(encoding="utf-8")

with open(r"E:\liuxiang\agnes_video_doc.json", "r", encoding="utf-8") as f:
    data = json.load(f)

blocks = data.get("block", {})

# Find the Chinese (zh-CN) version - look for language markers
# First, let's find all unique languages
langs = set()
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            props = val.get("properties", {})
            raw = json.dumps(props, ensure_ascii=False)
            if "lang" in str(block_data):
                langs.add(str(block_data.get("lang", "")))

# Check page entries for language info
page_entries = data.get("pageEntries", [])
zh_pages = [p for p in page_entries if p.get("lang") == "zh-CN"]
print(f"Chinese pages: {len(zh_pages)}")
for p in zh_pages[:5]:
    print(f"  {p.get('title')} - slug: {p.get('slug')} - pageId: {p.get('pageId')}")

# Now let's extract ALL text content from the main document blocks
# Focus on finding response fields section
print("\n\n=== ALL BLOCKS (compact) ===")
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            block_type = val.get("type", "")
            props = val.get("properties", {})
            title = val.get("title", "")
            
            # Extract text
            text = ""
            if isinstance(title, list):
                for item in title:
                    if isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, str):
                                text += sub
            
            # Also check props
            props_text = ""
            for k, v in props.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, list):
                            for sub in item:
                                if isinstance(sub, str):
                                    props_text += sub + " "
                        elif isinstance(item, str):
                            props_text += item + " "
            
            combined = text or props_text
            if combined.strip():
                print(f"[{block_type}] {combined.strip()[:300]}")
