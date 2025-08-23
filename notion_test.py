import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_API_KEY"))

def extract_text(blocks, depth=0):
    out = []
    for b in blocks:
        t = b.get("type")
        data = b.get(t, {})

        # grab any rich_text content
        if "rich_text" in data:
            text = "".join([r.get("plain_text", "") for r in data["rich_text"]])
            if text.strip():
                out.append("  " * depth + text)

        # if this block has children, fetch them too
        if b.get("has_children"):
            child_id = b["id"]
            children = notion.blocks.children.list(block_id=child_id).get("results", [])
            out.append(extract_text(children, depth + 1))
    return "\n".join([x for x in out if x])

page_ids = [pid.strip() for pid in os.getenv("NOTION_PAGE_IDS", "").split(",") if pid.strip()]
for pid in page_ids:
    blocks = notion.blocks.children.list(block_id=pid).get("results", [])
    print(f"Raw blocks for page {pid}:", blocks)  # Debug print the raw block data
    text = extract_text(blocks)
    print(f"--- PAGE {pid} ---")
    print(text[:400])
    print()
