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
    page_title="Sunbeam RAG Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Sunbeam Chatbot")
st.caption("Answers strictly based on Sunbeam PDFs")

st.divider()

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdfs_ingested" not in st.session_state:
    st.session_state.pdfs_ingested = False

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
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("sunbeam_docs")

# =========================
# PDF INGESTION (AUTO)
# =========================
def ingest_pdfs_once(pdf_folder="pdfs"):
    if not os.path.exists(pdf_folder):
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    for file in os.listdir(pdf_folder):
        if not file.lower().endswith(".pdf"):
            continue

        loader = PyPDFLoader(os.path.join(pdf_folder, file))
        pages = loader.load()
        docs = splitter.split_documents(pages)

        documents, metadatas, ids = [], [], []

        for doc in docs:
            documents.append(doc.page_content)
            metadatas.append({
                "source": file,
                "page": doc.metadata.get("page", 0)
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
# AUTO INGEST ON START
# =========================
if not st.session_state.pdfs_ingested:
    with st.spinner("📄 Indexing PDFs..."):
        ingest_pdfs_once("pdfs")
        st.session_state.pdfs_ingested = True

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.subheader("💬 Chat History")

    if not st.session_state.messages:
        st.info("No questions yet")
    else:
        i = 0
        q_no = 1

        while i < len(st.session_state.messages):
            msg = st.session_state.messages[i]

            if msg["role"] == "user":
                with st.expander(f"Q{q_no}: {msg['content'][:50]}"):
                    st.write(msg["content"])

                    action = st.selectbox(
                        "Action",
                        ["Keep", "Delete"],
                        key=f"delete_{i}"
                    )

                    if action == "Delete":
                        del st.session_state.messages[i:i + 2]
                        st.rerun()

                q_no += 1
                i += 2
            else:
                i += 1

    st.divider()

    if st.button("🆕 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("📄 PDFs auto-loaded from `pdfs/` folder")

# =========================
# MAIN CHAT WINDOW
# =========================
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# =========================
# USER INPUT
# =========================
user_input = st.chat_input(
    "Ask about courses, internship, fees, duration..."
)

if user_input:
    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # =========================
    # RAG RETRIEVAL
    # =========================
    query_embedding = embed_model.embed_query(user_input)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=6
    )

    retrieved_docs = results["documents"][0] if results["documents"] else []
    context = "\n\n".join(retrieved_docs)

    # =========================
    # STRICT PROMPT
    # =========================
    prompt = f"""
You are an academic counselor chatbot for Sunbeam Institute.

RULES:
- Answer ONLY using the CONTEXT
- No outside knowledge
- If not found, say:
  "The requested information is not available in the provided documents."

Context:
{context}

User Question:
{user_input}

Final Answer:
"""

    response = llm.invoke(prompt)

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": response.content
    })

    st.rerun()
