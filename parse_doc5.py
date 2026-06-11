import json, sys

sys.stdout.reconfigure(encoding="utf-8")

with open(r"E:\liuxiang\agnes_video_doc.json", "r", encoding="utf-8") as f:
    data = json.load(f)

blocks = data.get("block", {})

# Get the response JSON example block
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            block_type = val.get("type", "")
            props = val.get("properties", {})
            
            if block_type == "code":
                title = val.get("title", "")
                text = ""
                if isinstance(title, list):
                    for item in title:
                        if isinstance(item, list):
                            for sub in item:
                                if isinstance(sub, str):
                                    text += sub
                if text.strip() and ("video_url" in text or "task_" in text or "video_" in text):
                    print(f"=== CODE BLOCK ===")
                    print(text[:2000])
                    print()
