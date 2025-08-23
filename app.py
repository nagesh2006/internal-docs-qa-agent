import os
import streamlit as st
from dotenv import load_dotenv
from notion_client import Client
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma

# -------------------
# Setup
# -------------------
load_dotenv()
notion = Client(auth=os.getenv("NOTION_API_KEY"))

# Cache embeddings + vectorstore
@st.cache_resource
def load_vectorstore():
    page_ids = [pid.strip() for pid in os.getenv("NOTION_PAGE_IDS", "").split(",") if pid.strip()]

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

    all_text = []
    for pid in page_ids:
        blocks = notion.blocks.children.list(block_id=pid).get("results", [])
        text = extract_text(blocks)
        all_text.append(text)

    docs_raw = "\n".join(all_text)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_text(docs_raw)

    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vs = Chroma.from_texts(docs, emb, persist_directory="./notion_chroma")

    return vs

vs = load_vectorstore()
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
# Streamlit UI
# -------------------
st.set_page_config(page_title="Internal Docs Q&A", page_icon="📚", layout="centered")
st.title("📚 Internal Docs Q&A Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything about company docs..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = ask(prompt)
        st.markdown(answer)
    st.session_state["messages"].append({"role": "assistant", "content": answer})
