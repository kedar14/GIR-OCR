import base64
from io import BytesIO
from PIL import Image as PILImage
import streamlit as st

# Conditional Imports
try:
    from mistralai import Mistral
    mistral_available = True
except ImportError:
    mistral_available = False

try:
    from google.cloud import vision
    google_available = True
except ImportError:
    google_available = False

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Custom Styles ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');

    * { font-family: 'Noto Sans', sans-serif; }

    .stApp {
        background: linear-gradient(to bottom, #f0f2f6, #fff);
    }

    .main-title {
        text-align: center;
        font-size: 48px !important;
        font-weight: bold;
        color: #333;
    }

    .sidebar .stRadio > label {
        font-size: 16px;
    }

    .success-box {
        border: 1px solid #4CAF50;
        padding: 10px;
        background-color: #d4edda;
        border-radius: 5px;
        color: #2B3641;
    }

    .error-box {
        border: 1px solid #f44336;
        padding: 10px;
        background-color: #f8d7da;
        border-radius: 5px;
        color: #2B3641;
    }

    .stButton > button {
        background-color: #4CAF50;
        color: white;
        padding: 14px 20px;
        margin: 8px 0;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
    }

    .stButton > button:hover {
        background-color: #3e8e41;
    }

    .stCodeBlock {
        background-color: #f5f5f5;
        border: 1px solid #ccc;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Sidebar Inputs ----
with st.sidebar:
    st.header("⚙️ API Configuration")

    api_provider = st.radio(
        "Select API Provider",
        ["Mistral", "Google Cloud Vision"],
        disabled=not (mistral_available or google_available),  # Disable if neither lib is installed
        help="Choose the OCR API you want to use. Requires API key and installation of necessary libraries.",
    )

    if not mistral_available and api_provider == "Mistral":
        st.warning("MistralAI library not installed. Please install it to use Mistral.", icon="⚠️")
    if not google_available and api_provider == "Google Cloud Vision":
        st.warning("Google Cloud Vision library not installed. Please install it to use Google.", icon="⚠️")

    if api_provider == "Mistral":
        api_key_label = "Mistral API Key"
        key_session_var = "mistral_api_key"
        creds_session_var = None  # no creds needed
    else:  # Google Cloud Vision
        api_key_label = "GCP Credentials (JSON)"
        key_session_var = "gcp_credentials"
        creds_session_var = "gcp_credentials"  # Used to get the api client

    # Persistent Storage
    if key_session_var not in st.session_state:
        st.session_state[key_session_var] = ""

    if api_provider == "Mistral":
        api_key = st.text_input(api_key_label, type="password", value=st.session_state[key_session_var],
                               help=f"Enter your {api_provider} API key.")
    else:  # google
        api_key = st.text_area(api_key_label, value=st.session_state[key_session_var],
                              help=f"Enter your {api_provider} credentials (JSON).")

    if st.button(f"💾 Save {api_provider} Key"):
        st.session_state[key_session_var] = api_key
        st.success(f"✅ {api_provider} Key saved for this session!", icon="✅")

    # API Client Initialization
    client_session_var = "client"
    if client_session_var not in st.session_state and st.session_state[key_session_var]:
        try:
            if api_provider == "Mistral":
                client = Mistral(api_key=st.session_state[key_session_var])
                st.session_state["client"] = client
                st.success("Mistral API Client Initialized!", icon="🤖")
            elif api_provider == "Google Cloud Vision" and google_available:  # Check for Google Cloud Vision availability
                try:  # Added try-except block for loading credentials
                    import json
                    credentials = json.loads(st.session_state[key_session_var])
                    client = vision.ImageAnnotatorClient.from_service_account_info(credentials)
                    st.session_state["client"] = client
                    st.success("Google Cloud Vision API Client Initialized!", icon="🤖")
                except json.JSONDecodeError:
                    st.error("Invalid GCP Credentials JSON. Please ensure the JSON is valid.", icon="🔥")
                    st.stop()
                except Exception as e:
                    st.error(f"Error initializing Google Cloud Vision client: {e}", icon="🔥")
                    st.stop()
            else:
                client = None
                st.session_state["client"] = client

        except Exception as e:
            st.error(f"Error initializing API client: {e}", icon="🔥")

    st.header("📁 File & Source Selection")
    file_type = st.radio("File Type", ["PDF", "Image"], help="Choose the type of file you want to process.")
    source_type = st.radio("Input Source", ["URL", "Local Upload"],
                           help="Select whether to upload a file or provide a URL.")

# ---- Main Header ----
st.markdown("<h1 class='main-title'>📄 Gir Reader 🦁</h1>", unsafe_allow_html=True)

# ---- OCR Input Handling ----
if source_type == "URL":
    input_url = st.text_input("File URL", placeholder="Enter URL here...",
                             help="Enter the URL of the PDF or image file.")
    uploaded_file = None
else:
    input_url = None
    uploaded_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "gif", "bmp", "pdf"],
                                     help="Upload a PDF or image file from your computer.")

# ---- Process Button ----
# Disable the button based on API provider, API key, and file/URL input
process_button = st.button(
    "🚀 Process Document",
    disabled=not (
            st.session_state.get(key_session_var)
            and (input_url or uploaded_file)
            and (
                    (api_provider == "Mistral" and mistral_available)
                    or (api_provider == "Google Cloud Vision" and google_available)
            )
    ),
)

if process_button:
    if not st.session_state[key_session_var]:
        st.error(f"❌ Please enter and save your {api_provider} API Key/Credentials.", icon="🔑")
    elif source_type == "URL" and not input_url:
        st.error("❌ Please enter a valid URL.", icon="🔗")
    elif source_type == "Local Upload" and uploaded_file is None:
        st.error("❌ Please upload a valid file.", icon="📁")
    else:
        try:
            client = st.session_state["client"]
            if client is None:
                st.error(f"❌ {api_provider} Client not initialized.  Please check your API key and library installation.", icon="🔥")
                st.stop()

            with st.spinner("🔍 Processing document..."):
                if api_provider == "Mistral":
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
                                st.error("❌ Unsupported image format. Please use PNG, JPEG, BMP, or GIF.", icon="🖼️")
                                st.stop()
                            mime_type = f"image/{format}"
                            document = {"type": "image_url", "image_url": f"data:{mime_type};base64,{encoded_file}"}

                    # Perform OCR
                    include_base64 = file_type != "PDF"
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document=document,
                        include_image_base64=include_base64,
                    )
                    pages = ocr_response.pages if hasattr(ocr_response, "pages") else []
                    ocr_result = "\n\n".join(page.markdown for page in pages) or "⚠️ No result found"

                elif api_provider == "Google Cloud Vision":
                    if not google_available:
                        st.error("Google Cloud Vision is not available. Please select Mistral or install the required libraries.")
                        st.stop()
                    # Handle Input Source
                    if source_type == "URL":
                        if file_type == "PDF":
                            st.error(
                                "❌ URL input for PDFs is not directly supported. Please upload the PDF.",
                                icon="⚠️")
                            st.stop()

                        image = vision.Image()
                        image.source.image_uri = input_url

                    else:
                        file_bytes = uploaded_file.read()
                        image = vision.Image(content=file_bytes)

                    # Perform OCR
                    if file_type == "PDF":
                        # Feature detection for PDFs (enterprise feature)
                        feature = vision.Feature(
                            type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION
                        )
                    else:
                        feature = vision.Feature(
                            type_=vision.Feature.Type.TEXT_DETECTION  # Detect text
                        )
                    request = vision.AnnotateImageRequest(image=image, features=[feature])
                    try:
                        response = client.annotate_image(request=request)  # Make the API request
                    except Exception as e:
                        st.error(f"Error during Google Cloud Vision API call: {e}", icon="🔥")
                        st.stop()

                    if file_type == "PDF":
                        ocr_result = response.full_text_annotation.text if response.full_text_annotation else "⚠️ No text found"  # Use full_text_annotation to get all the text
                    else:
                        ocr_result = response.text_annotations[
                            0].description if response.text_annotations else "⚠️ No text found"  # Use text_annotations to get all the text

                else:
                    ocr_result = "No API provider selected."

            # Store OCR result
            st.session_state["ocr_result"] = ocr_result

            # Display OCR Result
            st.success("📃 OCR Result:", icon="✅")
            st.code(ocr_result, language="markdown")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}", icon="🔥")

# ---- Options After OCR ----
if "ocr_result" in st.session_state:
    action = st.radio("What would you like to do next?",
                      ["🔧 Refine Input Text", "🌎 Translate to English"])

    if action == "🔧 Refine Input Text":
        if st.button("🔧 Refine Text Now"):
            try:
                # Placeholder refinement. Needs actual refinement code (LLM).
                refined_text = st.session_state['ocr_result']
                st.session_state["refined_text"] = refined_text
                st.success("📑 Refined OCR Text:", icon="✅")
                st.code(refined_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Refinement error: {str(e)}", icon="🔥")

    if action == "🌎 Translate to English":
        if st.button("🌎 Translate Now"):
            try:
                # Placeholder translation. Needs actual translation code (Translation API or LLM).
                translated_text = st.session_state['ocr_result']
                st.session_state["translated_text"] = translated_text
                st.success("🌍 Translated Text:", icon="✅")
                st.code(translated_text, language="markdown")

            except Exception as e:
                st.error(f"❌ Translation error: {str(e)}", icon="🔥")

# ---- Advanced Process (Summarize in 5 Points) ----
if "translated_text" in st.session_state and st.button("⚡ Advanced Process"):
    try:
        # Placeholder summarization. Needs actual summarization code (LLM).
        summary_text = "Summary Placeholder"
        st.success("📌 Key Takeaways:", icon="✅")
        st.code(summary_text, language="markdown")

    except Exception as e:
        st.error(f"❌ Summary error: {str(e)}", icon="🔥")
