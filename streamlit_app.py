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
            else:  # Google Cloud Vision
                import json
                credentials = json.loads(st.session_state[key_session_var])
                client = vision.ImageAnnotatorClient.from_service_account_info(credentials)
                st.session_state["client"] = client
                st.success("Google Cloud Vision API Client Initialized!", icon="🤖")
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
                            if format not in ["jpeg", "png", "bmp
