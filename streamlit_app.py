import base64
import re
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st
from mistralai import Mistral

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Custom Styles (Noto Sans + Ancient Yellow Background) ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
    * { font-family: 'Noto Sans', sans-serif; }
    .stApp { background-color: #f7b267; } /* Ancient Yellow */
    .main { text-align: center; }
    .big-font { font-size:20px !important; font-weight: bold; }
    .success-box { border: 2px solid green; padding: 10px; background-color: #e6ffe6; border-radius: 5px; }
    .error-box { border: 2px solid red; padding: 10px; background-color: #ffe6e6; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# ---- Sidebar Inputs ----
st.sidebar.header("🔑 API Configuration")

# Persistent API Key Storage
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

api_key = st.sidebar.text_input("Enter Mistral API Key", type="password", value=st.session_state["api_key"])

if st.sidebar.button("💾 Save API Key"):
    st.session_state["api_key"] = api_key
    st.success("✅ API Key saved for this session!")

# Ensure API client initialization
if "client" not in st.session_state and st.session_state["api_key"]:
    st.session_state["client"] = Mistral(api_key=st.session_state["api_key"])

st.sidebar.header("📁 File & Source Selection")
file_type = st.sidebar.radio("Select File Type", ["PDF", "Image"])
source_type = st.sidebar.radio("Choose Input Source", ["URL", "Local Upload"])

# ---- Main Header ----
st.markdown("<h1 class='main big-font'>📄 Mistral OCR & Translation Tool</h1>", unsafe_allow_html=True)
st.markdown("<h1 class='main big-font'>📄 Gir Reader 🦁 </h1>", unsafe_allow_html=True)

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
        st.error("❌ Please enter and save a valid API Key.")
    elif source_type == "URL" and not input_url:
        st.error("❌ Please enter a valid URL.")
    elif source_type == "Local Upload" and uploaded_file is None:
        st.error("❌ Please upload a valid file.")
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
                    document = {"type": "document_file", "file_content": encoded_file}
                else:
                    img = PILImage.open(BytesIO(file_bytes))
                    format = img.format.lower()
                    if format not in ["jpeg", "png", "bmp", "gif"]:
                        st.error("❌ Unsupported image format. Please use PNG, JPEG, BMP, or GIF.")
                        st.stop()
                    mime_type = f"image/{format}"
                    document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_file}"}

            # Perform OCR
            with st.spinner("🔍 Processing document..."):
                include_base64 = file_type != "PDF"
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document=document,
                    include_image_base64=include_base64,
                )
                pages = ocr_response.pages if hasattr(ocr_response, "pages") else []
                ocr_result = "\n\n".join(page.markdown for page in pages) or "⚠️ No result found"

            # Store OCR result
            st.session_state["ocr_result"] = ocr_result

            # Display OCR Result
            st.success("📃 OCR Result:")
            st.code(ocr_result, language="markdown")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ---- Options After OCR ----
if "ocr_result" in st.session_state:
    action = st.radio("What would you like to do next?", ["🔧 Refine Input Text", "🌎 Translate to English"])

    if action == "🔧 Refine Input Text":
        if st.button("🔧 Refine Text Now"):
            try:
                client = st.session_state["client"]
                with st.spinner("🛠 Refining OCR Text..."):
                    response = client.chat.complete(
                        model="mistral-large-latest",
                        messages=[{"role": "user", "content": f"Improve the structure and readability of the following text:\n\n{st.session_state['ocr_result']}"}],
                    )
                    refined_text = response.choices[0].message.content

                st.session_state["refined_text"] = refined_text
                st.success("📑 Refined OCR Text:")
                st.code(refined_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Refinement error: {str(e)}")

    if action == "🌎 Translate to English":
        if st.button("🌎 Translate Now"):
            try:
                client = st.session_state["client"]
                with st.spinner("🔄 Translating..."):
                    response = client.chat.complete(
                        model="mistral-large-latest",
                        messages=[{"role": "user", "content": f"Translate the following text to English:\n\n{st.session_state['ocr_result']}"}],
                    )
                    translated_text = response.choices[0].message.content

                st.session_state["translated_text"] = translated_text
                st.success("🌍 Translated Text:")
                st.code(translated_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Translation error: {str(e)}")

# ---- Advanced Process (Summarize in 5 Points) ----
if "translated_text" in st.session_state and st.button("⚡ Advanced Process"):
    try:
        client = st.session_state["client"]
        with st.spinner("🔄 Summarizing text into key points..."):
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": f"Summarize the following translated text into 5 key bullet points:\n\n{st.session_state['translated_text']}"}],
            )
            summary_text = response.choices[0].message.content

        st.success("📌 Key Takeaways:")
        st.code(summary_text, language="markdown")

    except Exception as e:
        st.error(f"❌ Summary error: {str(e)}")
