import streamlit as st
import google.generativeai as genai
import os
from PyPDF2 import PdfReader
from docx import Document
import time  # For getting current time (optional for "Uploaded just now")

# --- Page Configuration ---
st.set_page_config(page_title="DocuSense AI", page_icon="📄")

# --- API Key ---
GOOGLE_API_KEY = ("AIzaSyBlzuF6xA2jKzTTywVU00nnCuauw7affPA") # Replace with your actual API key or secure method
genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-2.0-flash"
model = genai.GenerativeModel(MODEL_NAME)

# --- Document Processing Functions (same as before) ---
def read_document_content(uploaded_file):
    file_type = uploaded_file.type
    content = ""
    try:
        if file_type == "text/plain":
            content = uploaded_file.read().decode("utf-8")
        elif file_type == "application/pdf":
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                content += page.extract_text()
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
        else:
            st.warning(f"Unsupported file type: {file_type}. Please upload .txt, .pdf, or .docx files.")
            return None
        return content
    except Exception as e:
        st.error(f"Error reading document: {e}")
        return None

def ask_gemini(document_content, user_question):
    prompt_parts = [
        "You are a helpful document assistant. if the document contains photo then explain about the photo.  Based on the content of the document provided, answer the user's question.you can convert any document into any language asked by the user .",
        "Document Content:\n" + document_content,
        "User Question:\n" + user_question,
    ]
    try:
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        st.error(f"Error communicating with Gemini: {e}")
        return "Sorry, I encountered an error while processing your question."

# --- Streamlit App UI ---
st.header("DocuSense AI 📄", divider=True)

# Document Management Title and Subtitle
st.title("Document Management")
st.write("Manage, analyze, and extract insights from your documents")

# --- Top Navigation Bar ---
col1, col2, col3, col4, col5, col_new_button, col_profile = st.columns([1,1,1,1,1, 0.5, 0.3])

with col1:
    if st.button("All Documents", use_container_width=True, key="all_docs_tab"):
        pass
with col2:
    if st.button("Recent", use_container_width=True, key="recent_tab"):
        pass
with col3:
    if st.button("PDFs", use_container_width=True, key="pdfs_tab"):
        pass
with col4:
    if st.button("Word Documents", use_container_width=True, key="word_docs_tab"):
        pass
with col_new_button:
    st.button("+ New", use_container_width=True, key="new_doc_button")
with col_profile:
    st.button("👤", use_container_width=True, key="profile_button")

# --- Search Bar ---
search_query = st.text_input("Search documents...", placeholder="Search documents...")

# --- Document Grid Display ---
st.write("---")

# Dummy Document Data (Single dummy document for initial state)
dummy_documents = [
    {"name": "Example Document.pdf", "type": "Pdf", "size": "1 MB", "uploaded": "Example", "tags": ["example", "dummy"], "status": True},
]

# Function to display a document card (now handles both dummy and uploaded doc info)
def display_document_card(doc_info):
    col_doc, col_status = st.columns([3, 1])

    with col_doc:
        if doc_info["type"] == "Pdf":
            icon = "📄"
        elif doc_info["type"] == "Docx":
            icon = "📝"
        elif doc_info["type"] == "Pptx":
            icon = "📊"
        elif doc_info["type"] == "txt":
            icon = "📄" # You might want a different icon for text files
        else:
            icon = "📎"

        st.markdown(f"{doc_info['name']}")
        st.write(f"{icon} {doc_info['type']} • {doc_info['size']}")
        st.write(f"Uploaded {doc_info['uploaded']}")
        if doc_info["tags"]:
            tags_str = ", ".join([f"{tag}" for tag in doc_info["tags"]])
            st.write(tags_str)

    with col_status:
        status_toggle = st.toggle("Status", value=doc_info["status"], key=f"status_{doc_info['name']}")


# --- File Uploader ---
uploaded_file = st.file_uploader("Upload a document (txt, pdf, docx)", type=["txt", "pdf", "docx"])

# Document Grid Display Logic
num_cols = 3
doc_cols = st.columns(num_cols)

if uploaded_file is not None:
    # Display uploaded document
    uploaded_doc_info = {
        "name": uploaded_file.name,
        "type": uploaded_file.type.split('/')[1] if '/' in uploaded_file.type else uploaded_file.type.split('.')[1] if '.' in uploaded_file.name else "Unknown", # Extract file type
        "size": f"{uploaded_file.size / (1024 * 1024):.1f} MB" if uploaded_file.size > 1024 * 1024 else f"{uploaded_file.size / 1024:.1f} KB", # Format size
        "uploaded": "Just now", # Or use datetime.now() and format
        "tags": [], # You can add tag extraction logic later
        "status": True # Default status
    }
    with doc_cols[0]: # Display uploaded document in the first column
        with st.container(border=True):
            display_document_card(uploaded_doc_info)

    # Display dummy document in the next column (optional, or remove if you only want uploaded doc)
    with doc_cols[1 % num_cols]: # Use modulo to cycle through columns if needed
        with st.container(border=True):
            display_document_card(dummy_documents[0]) # Display the single dummy document

else:
    # Display dummy documents when no file is uploaded initially
    for index, doc in enumerate(dummy_documents):
        with doc_cols[index % num_cols]:
            with st.container(border=True):
                display_document_card(doc)


st.write("---") # Separator before file preview and chat


if uploaded_file is not None:
    document_content = read_document_content(uploaded_file)

    if document_content:
        st.subheader("Document Preview")
        st.text_area("Document Content", value=document_content, height=300)

        st.subheader("Chat with Document")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_question = st.chat_input("Ask a question about the document:")
        if user_question:
            with st.chat_message("user"):
                st.markdown(user_question)
                st.session_state.chat_history.append({"role": "user", "content": user_question})

            gemini_response = ask_gemini(document_content, user_question)

            with st.chat_message("assistant"):
                st.markdown(gemini_response)
                st.session_state.chat_history.append({"role": "assistant", "content": gemini_response})

else:
    st.info("Please upload a document to start.")

# --- Footer (Optional) ---
st.markdown("---")
st.write("Made with codesprint")