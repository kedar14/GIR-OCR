import base64
import re
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st

# ---- Attempt to Import Google Cloud Vision ----
google_vision_available = True
try:
    from google.cloud import vision
    from google.oauth2 import service_account
except ImportError:
    google_vision_available = False

# ---- Attempt to Import Mistral API ----
mistral_available = True
try:
    from mistralai import Mistral
except ImportError:
    mistral_available = False

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Custom Styles (Noto Sans + Tibetan Light Painting Background) ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
    
    * { font-family: 'Noto Sans', sans-serif; }
    
    .stApp { 
        background-image: url('https://upload.wikimedia.org/wikipedia/commons/6/6e/Tibetan_Mandala.jpg'); 
        background-size: cover; 
        background-position: center; 
    }
    
    .main-title {
        text-align: center;
        font-size: 60px !important; /* 3x increase */
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Sidebar Inputs ----
st.sidebar.header("🔑 API Configuration")

# Google Vision API Key Input
google_api_key = st.sidebar.text_area("Enter Google Vision API Key (JSON)", height=100)

# Mistral API Key Storage
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key = st.sidebar.text_input("Enter Mistral API Key", type="password", value=st.session_state["api_key"])

if st.sidebar.button("💾 Save API Keys"):
    st.session_state["api_key"] = api_key
    st.session_state["google_api_key"] = google_api_key
    st.success("✅ API Keys saved for this session!")

# Ensure API client initialization if Mistral is available
if mistral_available and "client" not in st.session_state and st.session_state["api_key"]:
    st.session_state["client"] = Mistral(api_key=st.session_state["api_key"])

st.sidebar.header("📁 File & Source Selection")
file_type = st.sidebar.radio("Select File Type", ["PDF", "Image"])
source_type = st.sidebar.radio("Choose Input Source", ["URL", "Local Upload"])

# ---- Select OCR Method ----
ocr_options = []
if mistral_available:
    ocr_options.append("Mistral AI")
if google_vision_available:
    ocr_options.append("Google Vision Pro")

ocr_method = st.sidebar.radio("Choose OCR Method", ocr_options)

# ---- Main Header ----
st.markdown("<h1 class='main-title'>📄 Gir Reader 🦁</h1>", unsafe_allow_html=True)

# ---- OCR Input Handling ----
if source_type == "URL":
    input_url = st.text_input("Enter File URL")
    uploaded_file = None
else:
    input_url = None
    uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "gif", "bmp", "pdf"])

# ---- Process Button ----
if st.button("🚀 Process Document"):
    if ocr_method == "Mistral AI" and not st.session_state["api_key"]:
        st.error("❌ Please enter and save a valid API Key for Mistral.")
    elif ocr_method == "Google Vision Pro" and not google_api_key:
        st.error("❌ Please enter your Google Vision API Key JSON.")
    elif source_type == "URL" and not input_url:
        st.error("❌ Please enter a valid URL.")
    elif source_type == "Local Upload" and uploaded_file is None:
        st.error("❌ Please upload a valid file.")
    else:
        try:
            ocr_result = "⚠️ No result found"

            if ocr_method == "Mistral AI":
                client = st.session_state["client"]
                file_bytes = uploaded_file.read() if uploaded_file else None
                encoded_file = base64.b64encode(file_bytes).decode("utf-8") if file_bytes else None

                document = {"type": "document_url", "document_url": input_url} if file_type == "PDF" else {
                    "type": "image_url",
                    "image_url": input_url,
                } if source_type == "URL" else {
                    "type": "document_file",
                    "file_content": encoded_file
                } if file_type == "PDF" else {
                    "type": "image_url",
                    "image_url": f"data:image/{PILImage.open(BytesIO(file_bytes)).format.lower()};base64,{encoded_file}"
                }

                with st.spinner("🔍 Processing document..."):
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document=document,
                        include_image_base64=(file_type != "PDF"),
                    )
                    pages = ocr_response.pages if hasattr(ocr_response, "pages") else []
                    ocr_result = "\n\n".join(page.markdown for page in pages) or "⚠️ No result found"

            elif ocr_method == "Google Vision Pro":
                credentials = service_account.Credentials.from_service_account_info(eval(google_api_key))
                vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                file_bytes = uploaded_file.read()
                image = vision.Image(content=file_bytes)

                with st.spinner("🔍 Processing document with Google Vision..."):
                    response = vision_client.text_detection(image=image)
                    texts = response.text_annotations
                    ocr_result = texts[0].description if texts else "⚠️ No text found"

            st.session_state["ocr_result"] = ocr_result
            st.session_state["ocr_method"] = ocr_method  # Store the method for later processes
            st.success("📃 OCR Result:")
            st.code(ocr_result, language="markdown")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ---- Process After OCR (Refine / Translate) ----
if "ocr_result" in st.session_state:
    action = st.radio("What would you like to do next?", ["🔧 Refine Input Text", "🌎 Translate to English"])

    if action == "🔧 Refine Input Text":
        if st.button("🔧 Refine Text Now"):
            try:
                if st.session_state["ocr_method"] == "Mistral AI":
                    client = st.session_state["client"]
                    with st.spinner("🛠 Refining OCR Text..."):
                        response = client.chat.complete(
                            model="mistral-large-latest",
                            messages=[{"role": "user", "content": f"Improve the readability of the following text:\n\n{st.session_state['ocr_result']}"}],
                        )
                        refined_text = response.choices[0].message.content
                else:
                    refined_text = "Refinement is not available for Google Vision Pro."

                st.session_state["refined_text"] = refined_text
                st.success("📑 Refined OCR Text:")
                st.code(refined_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Refinement error: {str(e)}")

    if action == "🌎 Translate to English":
        if st.button("🌎 Translate Now"):
            try:
                if st.session_state["ocr_method"] == "Mistral AI":
                    client = st.session_state["client"]
                    with st.spinner("🔄 Translating..."):
                        response = client.chat.complete(
                            model="mistral-large-latest",
                            messages=[{"role": "user", "content": f"Translate this to English:\n\n{st.session_state['ocr_result']}"}],
                        )
                        translated_text = response.choices[0].message.content
                else:
                    translated_text = "Translation is not available for Google Vision Pro."

                st.session_state["translated_text"] = translated_text
                st.success("🌍 Translated Text:")
                st.code(translated_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Translation error: {str(e)}")
