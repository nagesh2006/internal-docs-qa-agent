# app.py
import os
import time
import streamlit as st
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma

# Local fetchers
from notion_fetcher import fetch_notion_docs
from fetch_gdocs import fetch_gdocs_docs

# -------------------
# Setup
# -------------------
load_dotenv()

st.set_page_config(page_title="Internal Docs Q&A", page_icon="📚", layout="centered")
st.title("📚 Internal Docs Q&A Chatbot")

# Sidebar filters
st.sidebar.title("⚙️ Settings")
sources = ["Notion", "Google Docs"]
selected_sources = st.sidebar.multiselect("Select sources", sources, default=sources)


# -------------------
# Vectorstore
# -------------------
@st.cache_resource
def load_vectorstore(source_names):
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    persist_dir = "./chroma_index"

    if os.path.exists(persist_dir) and len(os.listdir(persist_dir)) > 0:
        return Chroma(persist_directory=persist_dir, embedding_function=emb)

    # Load docs from chosen sources
    docs = []
    if "Notion" in source_names:
        notion_docs = fetch_notion_docs()
        docs.extend([d["text"] for d in notion_docs])

    if "Google Docs" in source_names:
        gdocs = fetch_gdocs_docs()
        docs.extend([d["text"] for d in gdocs])

    if not docs:
        st.error("⚠️ No documents loaded. Please check your sources.")
        return None

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = []
    for d in docs:
        chunks.extend(splitter.split_text(d))

    # Build & persist vectorstore
    vs = Chroma.from_texts(chunks, emb, persist_directory=persist_dir)
    vs.persist()
    return vs


vs = load_vectorstore(selected_sources)
llm = ChatOllama(model="gemma:2b-instruct-q4_0")


# -------------------
# Conversation Memory
# -------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []


def render_typing(message: str):
    """Typing animation for assistant replies."""
    placeholder = st.empty()
    typed_text = ""
    for char in message:
        typed_text += char
        placeholder.markdown(typed_text)
        time.sleep(0.015)


def ask(query):
    hits = vs.similarity_search(query, k=3) if vs else []
    context = "\n".join([h.page_content for h in hits])

    memory_context = "\n".join(
        [
            f"User: {m['content']}" if m["role"] == "user" else f"Assistant: {m['content']}"
            for m in st.session_state["messages"]
        ]
    )

    prompt = f"""You are an assistant that answers using company docs.

Conversation so far:
{memory_context}

Context:
{context}

Question: {query}
Answer:"""

    resp = llm.invoke(prompt)
    return resp.content


# -------------------
# Streamlit UI
# -------------------
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything about company docs..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = ask(prompt)
        render_typing(answer)
    st.session_state["messages"].append({"role": "assistant", "content": answer})