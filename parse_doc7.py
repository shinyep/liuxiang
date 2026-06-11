import json, sys

sys.stdout.reconfigure(encoding="utf-8")

with open(r"E:\liuxiang\agnes_video_doc.json", "r", encoding="utf-8") as f:
    data = json.load(f)

blocks = data.get("block", {})

# Check all block types
types = {}
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            bt = val.get("type", "unknown")
            types[bt] = types.get(bt, 0) + 1

print("Block types:", json.dumps(types, indent=2))

# Find code blocks - they might use a different structure
for block_id, block_data in blocks.items():
    raw = json.dumps(block_data, ensure_ascii=False)
    if "code" in raw.lower()[:200] and ("curl" in raw or "video_url" in raw or "task_" in raw):
        val = block_data.get("value", {}).get("value", {})
        print(f"\n=== Block {block_id} ===")
        print(json.dumps(val, ensure_ascii=False)[:2000])
