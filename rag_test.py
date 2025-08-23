import os
from dotenv import load_dotenv
from notion_client import Client
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma

load_dotenv()
notion = Client(auth=os.getenv("NOTION_API_KEY"))

# -------------------
# 1) fetch notion pages
# -------------------
def extract_text(blocks, depth=0):
    out = []
    for b in blocks:
        t = b.get("type")
        data = b.get(t, {})
        if "rich_text" in data:
            text = "".join([r.get("plain_text", "") for r in data["rich_text"]])
            if text.strip():
                out.append(text)
        if b.get("has_children"):
            child_id = b["id"]
            children = notion.blocks.children.list(block_id=child_id).get("results", [])
            out.append(extract_text(children, depth + 1))
    return "\n".join([x for x in out if x])

page_ids = [pid.strip() for pid in os.getenv("NOTION_PAGE_IDS", "").split(",") if pid.strip()]

all_text = []
for pid in page_ids:
    blocks = notion.blocks.children.list(block_id=pid).get("results", [])
    text = extract_text(blocks)
    all_text.append(text)

docs_raw = "\n".join(all_text)

# -------------------
# 2) chunk + embed
# -------------------
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_text(docs_raw)

emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vs = Chroma.from_texts(docs, emb, persist_directory="./notion_chroma")

# -------------------
# 3) query function
# -------------------
llm = ChatOllama(model="gemma:2b")

def ask(query):
    hits = vs.similarity_search(query, k=3)
    context = "\n".join([h.page_content for h in hits])
    prompt = f"""You are an assistant that answers questions using company docs.
Context:
{context}

Question: {query}
Answer:"""
    resp = llm.invoke(prompt)
    return resp.content

# -------------------
# 4) demo
# -------------------
if __name__ == "__main__":
    while True:
        q = input("❓ Ask a question (or 'quit'): ")
        if q.lower() in ["quit", "exit"]:
            break
        ans = ask(q)
        print("💡 Answer:", ans, "\n")
