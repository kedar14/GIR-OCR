import base64
import re
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st
from mistralai import Mistral

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Modern Minimalist UI ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #f9f9f9;
        color: #333;
        padding: 20px;
    }
    
    h1 {
        text-align: center;
        font-size: 36px;
        font-weight: 600;
        color: #222;
    }
    
    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    .stButton>button {
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        background: #007aff;
        color: white;
        border: none;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background: #005bb5;
    }
    
    input, textarea {
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #ccc;
        width: 100%;
    }
    
    pre {
        background: #f0f0f0;
        padding: 10px;
        border-radius: 8px;
        font-size: 14px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Main Header ----
st.markdown("<h1>📄 Gir Reader 🦁</h1>", unsafe_allow_html=True)

# ---- API Key Input ----
st.markdown("<div class='card'>🔑 <b>API Configuration</b></div>", unsafe_allow_html=True)
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""
api_key = st.text_input("Enter Mistral API Key", type="password", value=st.session_state["api_key"])
if st.button("💾 Save API Key"):
    st.session_state["api_key"] = api_key
    st.success("✅ API Key saved for this session!")
if "client" not in st.session_state and api_key:
    st.session_state["client"] = Mistral(api_key=api_key)

# ---- File Upload ----
st.markdown("<div class='card'>📁 <b>Upload File</b></div>", unsafe_allow_html=True)
file_type = st.radio("Select File Type", ["PDF", "Image"], horizontal=True)
source_type = st.radio("Choose Input Source", ["Local Upload", "URL"], horizontal=True)
if source_type == "URL":
    input_url = st.text_input("Enter File URL")
    uploaded_file = None
else:
    input_url = None
    uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "gif", "bmp", "pdf"])

# ---- Process Button ----
if st.button("🚀 Process Document"):
    if not st.session_state["api_key"]:
        st.markdown("<div class='card'>❌ Please enter and save a valid API Key.</div>", unsafe_allow_html=True)
    elif source_type == "URL" and not input_url:
        st.markdown("<div class='card'>❌ Please enter a valid URL.</div>", unsafe_allow_html=True)
    elif source_type == "Local Upload" and uploaded_file is None:
        st.markdown("<div class='card'>❌ Please upload a valid file.</div>", unsafe_allow_html=True)
    else:
        try:
            client = st.session_state["client"]
            if source_type == "URL":
                document = {"type": "document_url", "document_url": input_url} if file_type == "PDF" else {"type": "image_url", "image_url": input_url}
            else:
                file_bytes = uploaded_file.read()
                encoded_file = base64.b64encode(file_bytes).decode("utf-8")
                if file_type == "PDF":
                    document = {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded_file}"}
                else:
                    img = PILImage.open(BytesIO(file_bytes))
                    format = img.format.lower()
                    if format not in ["jpeg", "png", "bmp", "gif"]:
                        st.markdown("<div class='card'>❌ Unsupported image format.</div>", unsafe_allow_html=True)
                        st.stop()
                    mime_type = f"image/{format}"
                    document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_file}"}
            with st.spinner("🔍 Processing document..."):
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document=document,
                    include_image_base64=True,
                )
                pages = ocr_response.pages if hasattr(ocr_response, "pages") else []
                ocr_result = "\n\n".join(page.markdown for page in pages) or "⚠️ No result found"
            st.session_state["ocr_result"] = ocr_result
            st.markdown(f"<div class='card'><h3>📃 OCR Result:</h3><pre>{ocr_result}</pre></div>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<div class='card'>❌ Error: {str(e)}</div>", unsafe_allow_html=True)
