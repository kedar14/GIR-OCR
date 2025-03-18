import base64
import re
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st
from mistralai import Mistral

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Modern Steve Jobs UI ----
st.markdown("""
    <style>
    /* Background */
    .stApp {
        background: linear-gradient(to right, #0f0f0f, #1c1c1c);
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Title */
    h1 {
        text-align: center;
        font-size: 42px;
        font-weight: 700;
        letter-spacing: -1px;
        color: white;
        margin-bottom: 20px;
    }

    /* Glassmorphism Card */
    .glass-box {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0px 4px 12px rgba(255, 255, 255, 0.05);
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        padding: 12px 25px;
        font-size: 18px;
        font-weight: bold;
        background: linear-gradient(to right, #007aff, #1e3c72);
        color: white;
        border: none;
        transition: 0.3s ease-in-out;
    }
    
    .stButton>button:hover {
        background: linear-gradient(to right, #1e3c72, #007aff);
        transform: scale(1.05);
    }

    /* Sidebar */
    .css-1aumxhk, .css-18e3th9 { background-color: #181818 !important; color: white; }

    /* Input Fields */
    input, textarea {
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 10px;
    }

    /* OCR Result */
    pre {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        font-size: 16px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Sidebar Inputs ----
st.sidebar.markdown("<h2>🔑 API Configuration</h2>", unsafe_allow_html=True)

if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key = st.sidebar.text_input("Enter Mistral API Key", type="password", value=st.session_state["api_key"])

if st.sidebar.button("💾 Save API Key"):
    st.session_state["api_key"] = api_key
    st.success("✅ API Key saved for this session!")

if "client" not in st.session_state and api_key:
    st.session_state["client"] = Mistral(api_key=api_key)

st.sidebar.markdown("<h2>📁 File & Source Selection</h2>", unsafe_allow_html=True)
file_type = st.sidebar.radio("Select File Type", ["PDF", "Image"])
source_type = st.sidebar.radio("Choose Input Source", ["URL", "Local Upload"])

# ---- Main Header ----
st.markdown("<h1>📄 Gir Reader 🦁</h1>", unsafe_allow_html=True)

# ---- OCR Input Handling ----
if source_type == "URL":
    input_url = st.text_input("Enter File URL")
    uploaded_file = None
else:
    input_url = None
    uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "gif", "bmp", "pdf"])

# ---- Process Button ----
if st.button("🚀 Process Document"):
    if not st.session_state["api_key"]:
        st.markdown("<div class='glass-box'>❌ Please enter and save a valid API Key.</div>", unsafe_allow_html=True)
    elif source_type == "URL" and not input_url:
        st.markdown("<div class='glass-box'>❌ Please enter a valid URL.</div>", unsafe_allow_html=True)
    elif source_type == "Local Upload" and uploaded_file is None:
        st.markdown("<div class='glass-box'>❌ Please upload a valid file.</div>", unsafe_allow_html=True)
    else:
        try:
            client = st.session_state["client"]

            # Handle Input Source
            if source_type == "URL":
                document = {"type": "document_url", "document_url": input_url} if file_type == "PDF" else {
                    "type": "image_url",
                    "image_url": input_url,
                }
            else:
                file_bytes = uploaded_file.read()
                encoded_file = base64.b64encode(file_bytes).decode("utf-8")

                if file_type == "PDF":
                    document = {"type": "document_url", "document_url": f"data:application/pdf;base64,{encoded_file}"}
                else:
                    img = PILImage.open(BytesIO(file_bytes))
                    format = img.format.lower()
                    if format not in ["jpeg", "png", "bmp", "gif"]:
                        st.markdown("<div class='glass-box'>❌ Unsupported image format.</div>", unsafe_allow_html=True)
                        st.stop()
                    mime_type = f"image/{format}"
                    document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_file}"}

            # Perform OCR
            with st.spinner("🔍 Processing document..."):
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document=document,
                    include_image_base64=True,
                )
                pages = ocr_response.pages if hasattr(ocr_response, "pages") else []
                ocr_result = "\n\n".join(page.markdown for page in pages) or "⚠️ No result found"

            # Store OCR result
            st.session_state["ocr_result"] = ocr_result

            # Display OCR Result
            st.markdown(f"<div class='glass-box'><h3>📃 OCR Result:</h3><pre>{ocr_result}</pre></div>", unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f"<div class='glass-box'>❌ Error: {str(e)}</div>", unsafe_allow_html=True)

# ---- Next Steps ----
if "ocr_result" in st.session_state:
    action = st.radio("What would you like to do next?", ["🔧 Refine Input Text", "🌎 Translate to English"])

    if action == "🔧 Refine Input Text" and st.button("🔧 Refine Text Now"):
        try:
            client = st.session_state["client"]
            with st.spinner("🛠 Refining OCR Text..."):
                response = client.chat.complete(
                    model="mistral-large-latest",
                    messages=[{"role": "user", "content": f"Improve the structure and readability of:\n\n{st.session_state['ocr_result']}"}],
                )
                refined_text = response.choices[0].message.content
            st.markdown(f"<div class='glass-box'><h3>📑 Refined OCR Text:</h3><pre>{refined_text}</pre></div>", unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"<div class='glass-box'>❌ Error: {str(e)}</div>", unsafe_allow_html=True)

