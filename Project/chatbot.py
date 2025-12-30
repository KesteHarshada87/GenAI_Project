import streamlit as st
import chromadb
import os
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model

# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(
    page_title="✨ Sunbeam Smart Assistant",
    layout="wide"
)

# =========================
# LIGHT CLASSY UI (NO BLUE)
# =========================
st.markdown("""
<style>
body {
    background-color: #f9fafb;
}

/* User message */
.stChatMessage[data-testid="user"] {
    background-color: #e6f7f4;
    border-radius: 18px;
    padding: 14px;
    color: #065f46;
    border-left: 6px solid #2dd4bf;
}

/* Assistant message */
.stChatMessage[data-testid="assistant"] {
    background-color: #fff7ed;
    border-radius: 18px;
    padding: 14px;
    color: #7c2d12;
    border-left: 6px solid #fb923c;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

.sidebar-title {
    font-size: 18px;
    font-weight: 600;
    color: #0f766e;
}

/* Buttons */
.stButton>button {
    background-color: #14b8a6;
    color: white;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.title(" 🤖 Sunbeam Smart Academic Assistant ")
st.caption("📚 Reliable answers powered only by Sunbeam Institute documents")
st.divider()

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdfs_ingested" not in st.session_state:
    st.session_state.pdfs_ingested = False

if "language" not in st.session_state:
    st.session_state.language = "English"

# =========================
# EMBEDDINGS
# =========================
embed_model = init_embeddings(
    model="huggingface:sentence-transformers/all-MiniLM-L6-v2"
)

# =========================
# LLM
# =========================
llm = init_chat_model(
    model="llama-3.3-70b-versatile",
    model_provider="groq",
    api_key=os.getenv("GROQ_API_KEY")
)

# =========================
# CHROMA DB
# =========================
DB_PATH = "./chroma_db"
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection = chroma_client.get_or_create_collection("sunbeam_docs")

# =========================
# PDF INGESTION (NO MESSAGE)
# =========================
def ingest_pdfs(pdf_folder="pdfs"):
    if not os.path.exists(pdf_folder):
        return

    existing = collection.get()
    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    for file in os.listdir(pdf_folder):
        if file.lower().endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_folder, file))
            pages = loader.load()
            chunks = splitter.split_documents(pages)

            documents, metadatas, ids = [], [], []

            for chunk in chunks:
                documents.append(chunk.page_content.strip())
                metadatas.append({
                    "source": file,
                    "page": chunk.metadata.get("page", 0)
                })
                ids.append(str(uuid.uuid4()))

            embeddings = embed_model.embed_documents(documents)

            collection.add(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )

# =========================
# AUTO INGEST
# =========================
if not st.session_state.pdfs_ingested:
    with st.spinner("📄 Preparing knowledge base..."):
        ingest_pdfs("pdfs")
        st.session_state.pdfs_ingested = True

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🌐 Chat Language</div>", unsafe_allow_html=True)

    lang_map = {
        "English": "English",
        "Hindi (हिंदी)": "Hindi",
        "Marathi (मराठी)": "Marathi"
    }

    selected_lang = st.selectbox(
        "Choose language",
        list(lang_map.keys()),
        index=list(lang_map.values()).index(st.session_state.language)
    )
    st.session_state.language = lang_map[selected_lang]

    st.divider()
    st.markdown("<div class='sidebar-title'>💬 Chat History</div>", unsafe_allow_html=True)

    if not st.session_state.messages:
        st.info("No conversations yet")
    else:
        i, q_no = 0, 1
        while i < len(st.session_state.messages):
            msg = st.session_state.messages[i]
            if msg["role"] == "user":
                with st.expander(f"Q{q_no}: {msg['content'][:60]}"):
                    st.write(msg["content"])
                    if st.selectbox("Action", ["Keep", "Delete"], key=f"del_{i}") == "Delete":
                        del st.session_state.messages[i:i+2]
                        st.rerun()
                q_no += 1
                i += 2
            else:
                i += 1

    st.divider()
    if st.button("🆕 Start New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =========================
# CHAT DISPLAY
# =========================
for msg in st.session_state.messages:
    icon = "🧑‍🎓" if msg["role"] == "user" else "🎓"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

# =========================
# USER INPUT
# =========================
user_input = st.chat_input(
    f"Ask your question in {st.session_state.language}..."
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    query_embedding = embed_model.embed_query(user_input)
    results = collection.query(query_embeddings=[query_embedding], n_results=8)

    context = "\n\n".join(results["documents"][0]) if results["documents"] else ""

    prompt = f"""
You are an academic counselor chatbot for Sunbeam Institute.

RULES:
- Answer ONLY using the CONTEXT
- Answer strictly in {st.session_state.language}
- If missing, say:
  "The requested information is not available in the provided documents."

Context:
{context}

Question:
{user_input}

Answer:
"""

    response = llm.invoke(prompt)

    st.session_state.messages.append(
        {"role": "assistant", "content": response.content}
    )
    st.rerun()