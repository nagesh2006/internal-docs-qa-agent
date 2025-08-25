import os
import time
import streamlit as st
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Local fetchers
from notion_fetcher import fetch_notion_docs
import fetch_gdocs

# -------------------
# Setup
# -------------------
load_dotenv()

st.set_page_config(page_title="Internal Docs Q&A", page_icon="📚", layout="centered")
st.title("📚 Internal Docs Q&A Chatbot")

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

    docs = []
    if "Notion" in source_names:
        notion_docs = fetch_notion_docs()
        docs.extend([d["text"] for d in notion_docs])

    if "Google Docs" in source_names:
        gdocs = fetch_gdocs.fetch_gdocs()
        docs.extend([d["text"] for d in gdocs])

    if not docs:
        st.error("⚠️ No documents loaded. Please check your sources.")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = []
    for d in docs:
        chunks.extend(splitter.split_text(d))

    vs = Chroma.from_texts(chunks, emb, persist_directory=persist_dir)
    vs.persist()
    return vs

vs = load_vectorstore(selected_sources)

# -------------------
# Hugging Face Chat Model (Mistral-7B)
# -------------------
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    st.error("⚠️ Missing HF_TOKEN in .env or Streamlit secrets!")
    st.stop()

chat_model = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    task="conversational",
    huggingfacehub_api_token=hf_token,
)

llm = ChatHuggingFace(llm=chat_model)

# -------------------
# Conversation Memory
# -------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

def render_typing(message: str):
    placeholder = st.empty()
    typed_text = ""
    for char in message:
        typed_text += char
        placeholder.markdown(typed_text)
        time.sleep(0.015)

def ask(query: str):
    hits = vs.similarity_search(query, k=3) if vs else []
    context = "\n".join([h.page_content for h in hits])

    # Build messages for conversational model
    messages = [SystemMessage(content="You are an assistant that answers using company docs.")]
    for m in st.session_state["messages"]:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))

    messages.append(
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}\nAnswer:")
    )

    resp = llm.invoke(messages)
    return resp.content if hasattr(resp, "content") else str(resp)

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
