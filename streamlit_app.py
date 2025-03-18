import base64
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st
from mistralai import Mistral

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Custom Styles (Light & Dark Mode) ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Noto Sans', sans-serif;
    }

    .stApp {
        background-color: var(--background-color);
    }

    .main {
        text-align: center;
    }

    .big-font {
        font-size: 60px !important;  /* 3x size */
        font-weight: bold;
    }

    .sub-header {
        font-size: 45px !important;  /* 3x size */
        font-weight: bold;
    }

    .text-box {
        font-size: 36px !important;  /* 3x size */
    }

    .success-box, .error-box {
        padding: 20px;
        border-radius: 10px;
        font-size: 36px;  /* 3x size */
    }

    .success-box {
        border: 4px solid #008000;
        background-color: #e6ffe6;
    }

    .error-box {
        border: 4px solid #ff0000;
        background-color: #ffe6e6;
    }

    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #1e1e1e;
        }
        .success-box {
            border: 4px solid #00ff00;
            background-color: #002200;
            color: #ffffff;
        }
        .error-box {
            border: 4px solid #ff5555;
            background-color: #330000;
            color: #ffffff;
        }
        .big-font {
            color: #ffffff;
        }
        .sub-header {
            color: #ffffff;
        }
        .text-box {
            color: #ffffff;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---- Sidebar Inputs ----
st.sidebar.header("🔑 API Configuration")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key = st.sidebar.text_input("Enter Mistral API Key", type="password", value=st.session_state["api_key"])

if st.sidebar.button("💾 Save API Key"):
    st.session_state["api_key"] = api_key
    st.success("✅ API Key saved for this session!")

if "client" not in st.session_state and api_key:
    st.session_state["client"] = Mistral(api_key=api_key)

# ---- Main Header ----
st.markdown("<h1 class='main big-font'>📄 Gir Reader 🦁</h1>", unsafe_allow_html=True)

# ---- File Upload ----
st.sidebar.header("📁 File & Source Selection")
file_type = st.sidebar.radio("Select File Type", ["Image", "PDF"], index=0)
source_type = st.sidebar.radio("Choose Input Source", ["Local Upload", "URL"], index=0)

input_url = None
uploaded_file = None

if source_type == "URL":
    input_url = st.text_input("Enter File URL", help="Paste the URL of the document or image.")
else:
    uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "gif", "bmp", "pdf"])

# ---- Process Button ----
if st.button("🚀 Process Document"):
    if not st.session_state["api_key"]:
        st.markdown("<div class='error-box'>❌ Please enter and save a valid API Key.</div>", unsafe_allow_html=True)
    elif source_type == "URL" and not input_url:
        st.markdown("<div class='error-box'>❌ Please enter a valid URL.</div>", unsafe_allow_html=True)
    elif source_type == "Local Upload" and uploaded_file is None:
        st.markdown("<div class='error-box'>❌ Please upload a valid file.</div>", unsafe_allow_html=True)
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
                        st.markdown("<div class='error-box'>❌ Unsupported image format.</div>", unsafe_allow_html=True)
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
            st.markdown("<div class='success-box'><h3 class='sub-header'>📃 OCR Result:</h3><pre class='text-box'>" + ocr_result + "</pre></div>", unsafe_allow_html=True)

        except Exception as e:
            st.markdown(f"<div class='error-box'>❌ Error: {str(e)}</div>", unsafe_allow_html=True)
