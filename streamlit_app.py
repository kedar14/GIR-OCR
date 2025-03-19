import base64
import re
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st

# ---- Hardcoded API Keys ----
MISTRAL_API_KEY = "5lIwuBZtsB3WtnVe3VrkEaYQSKmKPy8i"  # 🔹 Replace with your actual Mistral API Key
GOOGLE_CREDENTIALS_JSON = """{
  "type": "service_account",
  "project_id": "gen-lang-client-0796491314",
  "private_key_id": "e9d06c2d524d323d95444baf08419f823ef52f02",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCXCznHO9vnWkQs\\n5k9dEZ1mB3FSUGFgqa8Q1BaUSDGooGegzcvrGYUkGcd8cFY/Um8nzg9mCHFA8Zhv\\nBwsbqEQIasYopbaJPwuGORE0ywtSrdlWyMUzB+mN249g7cCrzcVpNUsEHNIEtNEQ\\n5Jp/XMRdsXX+iUpQPVqDSmpReZ2pUBc4ixqM5OM7DPUGMPH3Y0T9/8ac51nQcMEd\\npFjKtsZrM7KSWYDkb1dosmX/I0zcbJS8p0XvtjhNwayLFw5Ja0tm/Qe0E4iCQ+7I\\nDdfnBSoZAMhNopD047ZrBzOa7JkRCfShxMb4ys8pV5T6+0pQVm0F8rIDe0Ve4EBd\\n9WD6aI7vAgMBAAECggEAIGlBQbZfjrp47KWTHCZ+fvlT4NTswGBI97R7D+CZ/1RE\\nSGZAvrcgMcnyW4qDh1z6CzGVblCbdNMi4ZhCUvH9f0ziLrC4haTopSmzvn9fc6No\\ngs3cOwIUpOMbVjJOaM9j8BqGeWBx1J60Sgqz+GaAoJZG+pKdRrCTrp6WR9tv8Hex\\njxDlpHlSG9DGAoR0AKGFlK7RS+QH9AG/v9yuL/dad6Sh+UcKBMapUC62OC4h1oxW\\nnk9W/VqHJTkVud12GnzfQZHEmp6eYc8c2qxJlTo4a2hUPKpRDm/MDYOoOVFSx6K0\\nJp5u2gfh+hbqeH4SJ3ebi2lr5zSEQP6Tzj0LVvht0QKBgQDUcX5nChlIrRzW8e8I\\nE2OnKmxK4uxKVc92LB4viozD+1BGOOUJYv9QgVlQGwF12j2Jz/AlKItAkbcAmist\\nmnpQhtELesX2SOr2wwtRjNKZSnKDUh9G866M1gGFp9juCF/SCO0zoyvW7y/hA9PU\\neTJV/VVSq0PFdD6w1eoifu9ydwKBgQC2Aw8p/iBw5tRJfWmR+6K8pEso9YmeA5nQ\\nv5n3SaNwbKobQM6IqC5dP0WZok0E2fyPfbpA7nXeBGEfVfxHpRyZ12WrgEs0ZNPQ\\nbiJbzPneBBRYzndxh5c8TuNjZ8okJPscCa1C5tG9aUS6VE+yd6qY/X4qV4kd/S8P\\n+xOSJY4tSQKBgQDJJXytSx6NdXts+T19w/4C9WP7s8hOydjY5wTdtq15kqZ7Frul\\nm5pqO065Thif4beKmNukEzNmO5GufEqNr0pInJ2p5OEzQ+9VHW/GEzQD+D1coZED\\nuQ54QtjGGBqJplwznkgZMFH9/BK1Vs5myyohyO/UilxsxJfnD2PUraNCGQKBgFfO\\nIgKgFgZhVQge+E70lg1rNNcNnNYd5pZN2HjzjWUvBuEe4oQKnlNdsrXrFjzA7JZM\\nkQ3B/BqfAjubv5jQjnuo7eNOgPlFquliODERMXlpfmdZM0YRo2P0qr3J1DqbnIhq\\nIqujrosxvXYmNkxibmpf3/2NPRi6i3mqJkba1zwBAoGARL7psJ6c4Vd+RRlBZpoi\\nW8W/ZhIQWr2qcSlrbwe7Z7ymFszuSF12Z+slWrSLXVluf4ZXEF/QbDwxzavXgHDH\\nEhScqKxAtgddfDb0XBcZoIrVdWvt60Fh3IXtsJjV9K3yRLM04lTIYIITjqvtNYsr\\n3I44BNrlMTJ8CUYRwys/izA=\\n-----END PRIVATE KEY-----\\n",
  "client_email": "kedar-patel@gen-lang-client-0796491314.iam.gserviceaccount.com",
  "client_id": "102456701662281837603",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/kedar-patel%40gen-lang-client-0796491314.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}"""
"""  # 🔹 Replace with Google Cloud JSON credentials

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
    if not MISTRAL_API_KEY and ocr_method == "Mistral AI":
        st.error("❌ Mistral API Key is missing. Please add it to the script.")
    elif not GOOGLE_CREDENTIALS_JSON and ocr_method == "Google Vision Pro":
        st.error("❌ Google Vision API Credentials are missing. Please add them to the script.")
    elif source_type == "URL" and not input_url:
        st.error("❌ Please enter a valid URL.")
    elif source_type == "Local Upload" and uploaded_file is None:
        st.error("❌ Please upload a valid file.")
    else:
        try:
            ocr_result = "⚠️ No result found"

            if ocr_method == "Mistral AI":
                client = Mistral(api_key=MISTRAL_API_KEY)
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
                credentials = service_account.Credentials.from_service_account_info(eval(GOOGLE_CREDENTIALS_JSON))
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

    if action == "🔧 Refine Input Text" or action == "🌎 Translate to English":
        if st.button("🔄 Process Now"):
            try:
                client = Mistral(api_key=MISTRAL_API_KEY)

                if action == "🔧 Refine Input Text":
                    task = "Improve the readability of the following text"
                else:
                    task = "Translate this to English"

                with st.spinner("🔄 Processing..."):
                    response = client.chat.complete(
                        model="mistral-large-latest",
                        messages=[{"role": "user", "content": f"{task}:\n\n{st.session_state['ocr_result']}"}],
                    )
                    processed_text = response.choices[0].message.content

                st.success(f"✅ {action} Result:")
                st.code(processed_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Processing error: {str(e)}")
