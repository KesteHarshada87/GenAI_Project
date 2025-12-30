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
st.set_page_config(page_title="🤖 Sunbeam RAG Chatbot", layout="wide")
st.title("🤖 Sunbeam Courses & Internship Chatbot")

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

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
# PDF INGESTION
# =========================
def ingest_pdfs(pdf_folder="pdfs"):
    if not os.path.exists(pdf_folder):
        st.warning("⚠️ 'pdfs' folder not found.")
        return 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    total_chunks = 0

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

        total_chunks += len(documents)

    return total_chunks

# =========================
# SIDEBAR (CHATGPT STYLE)
# =========================
with st.sidebar:
    st.header("💬 Chat History")

    if st.session_state.messages:
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"• {msg['content'][:60]}")

    st.markdown("---")
    st.header("📂 PDF Management")

    if st.button("📥 Ingest PDFs"):
        count = ingest_pdfs("pdfs")
        st.success(f"✅ {count} chunks ingested")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.success("Chat history cleared")

# =========================
# MAIN CHAT DISPLAY
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# USER INPUT
# =========================
user_input = st.chat_input("Ask about courses, internship, fees, duration...")

if user_input:
    # Store user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

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
    # CONVERSATION MEMORY
    # =========================
    conversation_history = ""
    for msg in st.session_state.messages[-8:]:
        conversation_history += f"{msg['role'].capitalize()}: {msg['content']}\n"

    # =========================
    # STRICT RAG PROMPT
    # =========================
    prompt = f"""
You are an academic counselor chatbot for Sunbeam Institute.

IMPORTANT RULES:
- Answer ONLY using the provided CONTEXT.
- DO NOT use any outside knowledge.
- If the answer is not found in the context, say:
  "The requested information is not available in the provided documents."

Conversation History:
{conversation_history}

Context:
{context}

User Question:
{user_input}

Final Answer:
"""

    response = llm.invoke(prompt)

    # Store assistant response
    st.session_state.messages.append(
        {"role": "assistant", "content": response.content}
    )

    with st.chat_message("assistant"):
        st.markdown(response.content)
