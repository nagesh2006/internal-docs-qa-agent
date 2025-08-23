from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama

texts = [
    ("refund", "Our refund policy allows returns within 30 days with proof of purchase."),
    ("design", "Request design assets via the Brand Portal; approvals happen in 2 business days."),
    ("security", "Report security incidents to sec-ops@example.com immediately."),
]

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
docs = []
for tag, txt in texts:
    for chunk in splitter.split_text(txt):
        docs.append(chunk)

emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vs = Chroma.from_texts(docs, emb, persist_directory="./chroma_db_test")
hits = vs.similarity_search("What's our refund policy?", k=1)
print("Top match:", hits[0].page_content)

llm = ChatOllama(model="gemma:2b")
resp = llm.invoke("Reply with the single word: READY")
print("LLM says:", resp.content)
