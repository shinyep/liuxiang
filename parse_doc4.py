import json, sys

sys.stdout.reconfigure(encoding="utf-8")

with open(r"E:\liuxiang\agnes_video_doc.json", "r", encoding="utf-8") as f:
    data = json.load(f)

blocks = data.get("block", {})

# Continue from where we left off - get remaining blocks
all_blocks = []
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            block_type = val.get("type", "")
            props = val.get("properties", {})
            title = val.get("title", "")
            
            text = ""
            if isinstance(title, list):
                for item in title:
                    if isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, str):
                                text += sub
                    elif isinstance(item, str):
                        text += item
            
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
                all_blocks.append((block_type, combined.strip()))

# Print from block 150 onwards (where we stopped)
for i, (bt, txt) in enumerate(all_blocks):
    if i >= 130:
        print(f"[{bt}] {txt[:400]}")
