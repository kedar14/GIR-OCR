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
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCXCznHO9vnWkQs\n5k9dEZ1mB3FSUGFgqa8Q1BaUSDGooGegzcvrGYUkGcd8cFY/Um8nzg9mCHFA8Zhv\nBwsbqEQIasYopbaJPwuGORE0ywtSrdlWyMUzB+mN249g7cCrzcVpNUsEHNIEtNEQ\n5Jp/XMRdsXX+iUpQPVqDSmpReZ2pUBc4ixqM5OM7DPUGMPH3Y0T9/8ac51nQcMEd\npFjKtsZrM7KSWYDkb1dosmX/I0zcbJS8p0XvtjhNwayLFw5Ja0tm/Qe0E4iCQ+7I\nDdfnBSoZAMhNopD047ZrBzOa7JkRCfShxMb4ys8pV5T6+0pQVm0F8rIDe0Ve4EBd\n9WD6aI7vAgMBAAECggEAIGlBQbZfjrp47KWTHCZ+fvlT4NTswGBI97R7D+CZ/1RE\nSGZAvrcgMcnyW4qDh1z6CzGVblCbdNMi4ZhCUvH9f0ziLrC4haTopSmzvn9fc6No\ngs3cOwIUpOMbVjJOaM9j8BqGeWBx1J60Sgqz+GaAoJZG+pKdRrCTrp6WR9tv8Hex\njxDlpHlSG9DGAoR0AKGFlK7RS+QH9AG/v9yuL/dad6Sh+UcKBMapUC62OC4h1oxW\nnk9W/VqHJTkVud12GnzfQZHEmp6eYc8c2qxJlTo4a2hUPKpRDm/MDYOoOVFSx6K0\nJp5u2gfh+hbqeH4SJ3ebi2lr5zSEQP6Tzj0LVvht0QKBgQDUcX5nChlIrRzW8e8I\nE2OnKmxK4uxKVc92LB4viozD+1BGOOUJYv9QgVlQGwF12j2Jz/AlKItAkbcAmist\nmnpQhtELesX2SOr2wwtRjNKZSnKDUh9G866M1gGFp9juCF/SCO0zoyvW7y/hA9PU\neTJV/VVSq0PFdD6w1eoifu9ydwKBgQC2Aw8p/iBw5tRJfWmR+6K8pEso9YmeA5nQ\nv5n3SaNwbKobQM6IqC5dP0WZok0E2fyPfbpA7nXeBGEfVfxHpRyZ12WrgEs0ZNPQ\nbiJbzPneBBRYzndxh5c8TuNjZ8okJPscCa1C5tG9aUS6VE+yd6qY/X4qV4kd/S8P\n+xOSJY4tSQKBgQDJJXytSx6NdXts+T19w/4C9WP7s8hOydjY5wTdtq15kqZ7Frul\nm5pqO065Thif4beKmNukEzNmO5GufEqNr0pInJ2p5OEzQ+9VHW/GEzQD+D1coZED\nuQ54QtjGGBqJplwznkgZMFH9/BK1Vs5myyohyO/UilxsxJfnD2PUraNCGQKBgFfO\nIgKgFgZhVQge+E70lg1rNNcNnNYd5pZN2HjzjWUvBuEe4oQKnlNdsrXrFjzA7JZM\nkQ3B/BqfAjubv5jQjnuo7eNOgPlFquliODERMXlpfmdZM0YRo2P0qr3J1DqbnIhq\nIqujrosxvXYmNkxibmpf3/2NPRi6i3mqJkba1zwBAoGARL7psJ6c4Vd+RRlBZpoi\nW8W/ZhIQWr2qcSlrbwe7Z7ymFszuSF12Z+slWrSLXVluf4ZXEF/QbDwxzavXgHDH\nEhScqKxAtgddfDb0XBcZoIrVdWvt60Fh3IXtsJjV9K3yRLM04lTIYIITjqvtNYsr\n3I44BNrlMTJ8CUYRwys/izA=\n-----END PRIVATE KEY-----\n",
  "client_email": "kedar-patel@gen-lang-client-0796491314.iam.gserviceaccount.com",
  "client_id": "102456701662281837603",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/kedar-patel%40gen-lang-client-0796491314.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}"""

# ---- Web App Configuration ----
st.set_page_config(page_title="Gir Reader", page_icon="📄", layout="centered")

# ---- Custom Styles ----
st.markdown("""
  <style>
    .stApp { 
        background-color: white; /* Sets a clean white background */
    }
    .main-title {
        text-align: center;
        font-size: 60px !important;  /* Ensures large title */
        font-weight: bold;
    }
  </style>
""", unsafe_allow_html=True)
