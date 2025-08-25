# 📚 Internal Docs Q&A Agent

An AI-powered assistant that answers company questions from **Notion + Google Docs** using **Retrieval-Augmented Generation (RAG)**.  
Runs with **Mistral-7B-Instruct** hosted on **Hugging Face Hub**, and provides an interactive chat UI via **Streamlit**.

---

## ✨ Features
- 🔗 Fetch docs from **Notion API** and **Google Docs API**
- ✂️ Smart **chunking & embeddings** via HuggingFace (`all-MiniLM-L6-v2`)
- 💾 Store & search efficiently with **ChromaDB**
- 🤖 Answer generation powered by **Mistral-7B-Instruct** (`mistralai/Mistral-7B-Instruct-v0.2`) from Hugging Face Hub
- 💬 Interactive **chat UI** built with Streamlit
- 🔒 Controlled access using **Hugging Face Inference API token**

---

## 🛠️ Tech Stack

| Layer          | Tool / Library                                |
|----------------|-----------------------------------------------|
| **Data Fetch** | Notion API, Google Docs API                   |
| **Embeddings** | HuggingFace (`all-MiniLM-L6-v2`)              |
| **Vector DB**  | ChromaDB                                      |
| **AI Engine**  | Hugging Face Hub (`mistralai/Mistral-7B-Instruct-v0.2`) |
| **Backend**    | LangChain + HuggingFaceEndpoint               |
| **Frontend**   | Streamlit                                     |

---

## 📦 Installation

### 1️⃣ Clone the repo

git clone https://github.com/nagesh2006/internal-docs-qa-agent.git
cd internal-docs-qa-agent

text

### 2️⃣ Create a virtual environment

python -m venv .venv

text

Activate it:

Mac/Linux

source .venv/bin/activate
Windows

.venv\Scripts\activate

text

### 3️⃣ Install dependencies

pip install -r requirements.txt

text

### 4️⃣ Setup Hugging Face
- Create a free account at [Hugging Face](https://huggingface.co)
- Go to **Settings > Access Tokens → Create a new token** with `"Read"` access  
- Add it to your `.env` file:

HF_TOKEN=your_huggingface_token

text

### 5️⃣ Setup Notion & Google Docs (optional)
In your `.env` file:

NOTION_API_KEY=your_notion_api_key
NOTION_PAGE_IDS=comma,separated,page_ids

GOOGLE_API_KEY=your_google_api_key
GOOGLE_DOC_IDS=comma,separated,doc_ids

text

---

## ▶️ Run the App

streamlit run app.py

text

Now open your browser at:  
👉 [**http://localhost:8501**](http://localhost:8501) 🎉

---

## 🤝 Contributing
- Fork the repo  
- Create a feature branch  

git checkout -b feature-name

text
- Commit changes & push  

git push origin feature-name

text
- Submit a Pull Request 🚀

---

## 📜 License
Licensed under the **MIT License**.  
Feel free to use, modify, and share.
