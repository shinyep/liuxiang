import urllib.request, json, sys

sys.stdout.reconfigure(encoding="utf-8")

req = urllib.request.Request("https://agnes-ai.com/api/doc/agnes-video-v20", headers={"Accept": "application/json"})
r = urllib.request.urlopen(req, timeout=30)
raw = r.read().decode("utf-8", "replace")
data = json.loads(raw)

# Save the full data
with open(r"E:\liuxiang\agnes_video_doc.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

blocks = data.get("block", {})
print(f"Total blocks: {len(blocks)}")

# Extract text content from blocks
def extract_text(val):
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        parts = []
        if "text" in val:
            t = val["text"]
            if isinstance(t, list):
                for item in t:
                    if isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, str):
                                parts.append(sub)
                            elif isinstance(sub, dict) and "string" in sub:
                                parts.append(sub["string"])
            elif isinstance(t, str):
                parts.append(t)
        if "content" in val:
            c = val["content"]
            if isinstance(c, str):
                parts.append(c)
        return " ".join(parts) if parts else str(val)[:200]
    if isinstance(val, list):
        return " ".join(str(v) for v in val)
    return str(val)

# Iterate through blocks and find relevant content
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            block_type = val.get("type", "")
            props = val.get("properties", {})
            title = val.get("title", "")
            
            # Look for heading blocks
            if block_type in ("heading1", "heading2", "heading3", "heading_1", "heading_2", "heading_3"):
                title_text = extract_text(title) if title else ""
                # Check the raw properties
                raw_props = json.dumps(props, ensure_ascii=False)[:500]
                if any(kw in raw_props.lower() for kw in ["响应", "response", "字段", "参数", "parameter", "request", "视频", "video"]):
                    print(f"\n--- {block_type}: {title_text} ---")
                    print(f"Props: {raw_props}")
            
            # Also check for text blocks with keywords
            raw_all = json.dumps(props, ensure_ascii=False)
            if any(kw in raw_all for kw in ["响应字段说明", "请求字段说明", "视频生成", "video/generations"]):
                print(f"\n--- Block {block_id} type={block_type} ---")
                print(json.dumps(props, ensure_ascii=False)[:1000])
