import json, sys

sys.stdout.reconfigure(encoding="utf-8")

with open(r"E:\liuxiang\agnes_video_doc.json", "r", encoding="utf-8") as f:
    data = json.load(f)

blocks = data.get("block", {})

# Let's look at all block types and their content
# First, find the page block to understand structure
for block_id, block_data in blocks.items():
    value = block_data.get("value", {})
    if isinstance(value, dict):
        val = value.get("value", value)
        if isinstance(val, dict):
            block_type = val.get("type", "")
            props = val.get("properties", {})
            title = val.get("title", "")
            content = val.get("content", [])
            
            # Extract all text from properties
            props_text = json.dumps(props, ensure_ascii=False)
            title_text = ""
            if isinstance(title, list):
                for item in title:
                    if isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, str):
                                title_text += sub
                            elif isinstance(sub, dict):
                                title_text += json.dumps(sub, ensure_ascii=False)
            
            # Print blocks with their types and text
            if block_type == "page":
                continue  # Skip the root page
            if title_text or props_text != "{}":
                # Only print if content is interesting
                combined = title_text + props_text
                if len(combined) > 2:
                    print(f"[{block_type}] {title_text[:200]} | props: {props_text[:300]}")
                    print()
