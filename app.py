import streamlit as st
import streamlit.components.v1 as components
import os
import re
import logging
from configparser import ConfigParser
from time import time
import urllib.parse
from logging.handlers import RotatingFileHandler

# === Logging ===
LOG_PATH = "/tmp/app.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# === Load settings ===
config = ConfigParser()
config.read("settings.config")

default_upload_path = config.get("files", "file_location", fallback="uploads")
default_output_path = config.get("files", "summary_location", fallback="results")
ollama_host_default = config.get("ollama", "host", fallback="localhost:11434")
ollama_model_default = config.get("ollama", "model_name", fallback="deepseek-r1:8b")
default_ai = config.get("general", "ai_to_use", fallback="ollama")

# === Page Setup ===
st.set_page_config(page_title="Convert IaC to Ansible", page_icon="🅰️", layout="wide")

# === Top UI ===
st.markdown("""
    <style>
    .top-header {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: #0f0f0f;
        padding: 10px 0 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .top-header img {
        max-width: 220px;
        height: auto;
    }
    .top-header .title {
        font-size: 20px;
        margin-top: 8px;
        color: white;
        font-weight: bold;
    }
    .top-header .version {
        font-size: 14px;
        color: #bbb;
        margin-top: 2px;
    }
    .loading-bar {
        height: 4px;
        background: linear-gradient(to right, #4facfe, #00f2fe);
        animation: loadbar 2s linear infinite;
    }
    @keyframes loadbar {
        0%   { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    </style>
    <div class="top-header">
        <a href="https://docs.ansible.com" target="_blank">
            <img src="https://github.com/ansible/logos/blob/main/community-usage/correct-use-white.png?raw=true" alt="Ansible Logo" />
        </a>
        <div class="title">Convert Puppet/Chef to Ansible Playbooks</div>
        <div class="version">v1.0.0</div>
    </div>
""", unsafe_allow_html=True)

# === Sidebar ===
st.sidebar.title("⚙️ Config Gen AI ")
ai_choice = st.sidebar.radio("Backend", ["ollama", "wxai", "maas"], index=0 if default_ai == "ollama" else 1)

if ai_choice == "ollama":
    from ai_modules.ollama_explanator import Ollama
    host = st.sidebar.text_input("Ollama Host", ollama_host_default)
    temp_ollama = Ollama(host=host)
    models = temp_ollama.list_models()
    model_dropdown = st.sidebar.selectbox("Model", models)
    model_name = model_dropdown.split(" (")[0].strip()
    st.sidebar.write(f"🔍 Using model: `{model_name}`")
    ai = Ollama(model_name=model_name, host=host)

elif ai_choice == "wxai":
    from ai_modules.wxai import WxAI
    ai = WxAI()

elif ai_choice == "maas":
    from ai_modules.maas_model import MaasModel
    st.sidebar.markdown("### 🔐 MaaS API Settings")
    maas_key = st.sidebar.text_input("API Key", type="password")
    maas_url = st.sidebar.text_input("Endpoint URL", value="https://granite-8b-code-instruct-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443")
    maas_model = st.sidebar.text_input("Model Name", value="granite-8b-code-instruct-128k")
    maas_stream = st.sidebar.checkbox("Enable Streaming Response", value=False)
    if maas_key and maas_url and maas_model:
        ai = MaasModel(api_key=maas_key, endpoint_url=maas_url, model_name=maas_model, stream=maas_stream)
    else:
        st.sidebar.warning("Please enter all MaaS details.")
        st.stop()

summary_path = st.sidebar.text_input("Output Folder", default_output_path)

# === File Selection ===
mode = st.radio("Choose File Source", ["Upload Files", "Browse Existing"])
files_to_process = []

if mode == "Upload Files":
    uploaded_files = st.file_uploader("Upload `.pp`, `.rb`, `.yml` files", type=["pp", "rb", "yml"], accept_multiple_files=True)
    if uploaded_files:
        files_to_process = uploaded_files
else:
    folder = st.text_input("Folder to browse", default_upload_path)
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder) if f.endswith(('.pp', '.rb', '.yml'))]
        selected = st.multiselect("Select files", all_files)
        files_to_process = [os.path.join(folder, f) for f in selected]

# === Process Files ===
if st.button("🚀 Convert to Ansible", disabled=not files_to_process):
    os.makedirs(summary_path, exist_ok=True)

    loading_placeholder = st.empty()
    loading_placeholder.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)

    total_files = len(files_to_process)
    progress = st.progress(0)

    for i, file in enumerate(files_to_process):
        filename = os.path.basename(file.name if hasattr(file, "name") else file)
        content = file.read().decode("utf-8") if hasattr(file, "read") else open(file, 'r').read()

        context = "Puppet module" if filename.endswith(".pp") else "Chef Recipe"
        logging.info(f"🔁 Calling backend: {ai.__class__.__name__} | Model: {getattr(ai, 'model_name', 'N/A')}")

        try:
            with st.spinner(f"⏳ Generating playbook for: {filename}..."):
                start = time()
                output = ai.transform(content, context)
                duration = time() - start

            match = re.search(r"```yaml\n(.*?)\n```", output, re.DOTALL)
            yaml_text = match.group(1) if match else output
            result_path = os.path.join(summary_path, f"{filename}.yaml")
            with open(result_path, 'w') as f:
                f.write(yaml_text)

            st.success(f"✅ {filename} processed in {duration:.1f}s")
            st.markdown(f"**Estimated tokens used**: {len(output.split())}")

            with st.expander(f"📂 {filename} – Click to View Playbook", expanded=False):
                unique_id = f"codeblock_{filename.replace('.', '_')}"
                encoded = urllib.parse.quote(yaml_text)

                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 6px;">
                        <button onclick="navigator.clipboard.writeText(document.getElementById('{unique_id}').innerText);"
                            title="Copy to Clipboard"
                            style="padding: 4px 6px; font-size: 12px; background-color: transparent; border: none; cursor: pointer;">
                            📋
                        </button>
                        <a href="data:text/yaml;charset=utf-8,{encoded}" download="{filename}.yaml" title="Download YAML">
                            <button style="padding: 4px 6px; font-size: 12px; background-color: transparent; border: none; cursor: pointer;">
                                ⬇️
                            </button>
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                components.html(f"""
                    <div id="{unique_id}" 
                         style="max-height: 400px; overflow-y: auto; border: 1px solid #555; border-radius: 8px; padding: 10px; background-color: #1e1e1e; color: white; font-family: monospace; font-size: 14px;">
                        <pre style="margin: 0;">{yaml_text}</pre>
                    </div>
                """, height=450)

        except Exception as e:
            st.error(f"❌ Error processing {filename}: {e}")
            logging.exception(f"Exception while processing {filename}")

        progress.progress((i + 1) / total_files)

    progress.progress(1.0)
    loading_placeholder.empty()
