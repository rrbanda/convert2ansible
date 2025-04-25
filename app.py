# app.py (Part 1 of N)
import streamlit as st
import streamlit.components.v1 as components
import os
import re
import logging
from configparser import ConfigParser
from time import time
import urllib.parse
import shutil
import tempfile
import subprocess
from typing import List

# === Safe logging for OpenShift environments ===
try:
    os.makedirs("/tmp/logs", exist_ok=True)
    logging_path = "/tmp/logs/app.log"
except Exception:
    logging_path = "app.log"
logging.basicConfig(filename=logging_path, level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# === Config loading ===
config = ConfigParser()
config.read("settings.config")
default_upload_path = config.get("files", "file_location", fallback="uploads")
default_output_path = config.get("files", "summary_location", fallback="results")
ollama_host_default = config.get("ollama", "host", fallback="localhost:11434")
ollama_model_default = config.get("ollama", "model_name", fallback="deepseek-r1:8b")
default_ai = config.get("general", "ai_to_use", fallback="maas")

# === Init session state ===
if "clone_status" not in st.session_state: st.session_state.clone_status = ""
if "cloned_repo_path" not in st.session_state: st.session_state.cloned_repo_path = ""
if "selected_git_folder" not in st.session_state: st.session_state.selected_git_folder = ""
if "git_files" not in st.session_state: st.session_state.git_files = []
if "selected_files" not in st.session_state: st.session_state.selected_files = []
if "available_tags" not in st.session_state: st.session_state.available_tags = []
if "filter_tags" not in st.session_state: st.session_state.filter_tags = []

# === UI setup ===
st.set_page_config(page_title="Convert IaC to Ansible", page_icon="🅰️", layout="wide")
st.markdown("""
<style>
    .top-header {
        position: sticky; top: 0; z-index: 1000;
        background-color: #0f0f0f; padding: 10px 0 20px;
        display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    .top-header img { max-width: 220px; height: auto; }
    .top-header .title { font-size: 20px; margin-top: 8px; color: white; font-weight: bold; }
    .top-header .version { font-size: 14px; color: #bbb; margin-top: 2px; }
    .loading-bar {
        height: 4px; background: linear-gradient(to right, #4facfe, #00f2fe);
        animation: loadbar 2s linear infinite;
    }
    @keyframes loadbar {
        0% { transform: translateX(-100%); }
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
# app.py (Part 2 of N)

# === Sidebar AI Settings ===
st.sidebar.title("⚙️ Config Gen AI")
# ai_choice = st.sidebar.radio("Backend", ["maas", "ollama", "agentic"], index=0)
ai_choice = st.sidebar.radio("Backend", ["maas", "agentic"], index=0)

# if ai_choice == "ollama":
#     from ai_modules.ollama_explanator import Ollama

#     host = st.sidebar.text_input("Ollama Host", ollama_host_default, key="ollama_host")

#     # Toggle in sidebar to show setup guide
#     show_setup = st.sidebar.checkbox("Show Ollama Setup Guide", value=False, key="show_ollama_guide")

#     # Simulate auto-scroll by jumping the anchor to top
#     if show_setup:
#         st.markdown('<a name="ollama_setup"></a>', unsafe_allow_html=True)
#         st.markdown("## 🛠️ How to Set Up Ollama Locally")
#         with st.expander("📘 Expand to View Setup Instructions", expanded=True):
#             st.markdown("""
#             1. 📦 **Install Ollama**
#             ```bash
#             curl -fsSL https://ollama.com/install.sh | sh
#             ```

#             2. 🚀 **Start the Ollama server**
#             ```bash
#             ollama serve
#             ```

#             3. 🧠 **Pull a model (e.g., llama3)**
#             ```bash
#             ollama pull llama3
#             ```

#             ✅ Confirm it's running at `http://localhost:11434` before using.
#             """)
#         st.markdown('<script>document.location.hash = "#ollama_setup";</script>', unsafe_allow_html=True)

#     # Attempt Ollama model connection
#     try:
#         temp_ollama = Ollama(host=host)
#         models = temp_ollama.list_models()
#         model_dropdown = st.sidebar.selectbox("Model", models, key="ollama_model")
#         model_name = model_dropdown.split(" (")[0].strip()
#         st.sidebar.success(f"🔍 Using model: `{model_name}`")
#         ai = Ollama(model_name=model_name, host=host)
#     except Exception as e:
#         st.sidebar.error(f"❌ Ollama not available.\n{e}")
#         st.stop()


if ai_choice == "maas":
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

elif ai_choice == "agentic":
    from ai_modules.agentic_model import AgenticModel
    maas_key = st.sidebar.text_input("MaaS API Key", type="password")
    maas_model = st.sidebar.text_input("Remote Model ID", value="granite-8b-code-instruct-128k")
    base_url = st.sidebar.text_input("LlamaStack Server URL", value="http://localhost:8321")

    if maas_key and maas_model and base_url:
        ai = AgenticModel(maas_key=maas_key, maas_model=maas_model, base_url=base_url)
    else:
        st.sidebar.warning("Please enter all required Agentic backend details.")
        st.stop()


summary_path = st.sidebar.text_input("Output Folder", default_output_path)

# === File Input Mode Selector (Only once)
file_source = st.radio("Choose File Source", ["Upload Files", "Browse Existing", "Git Repo"], key="file_source_radio")

# === Git Repo UI logic
if file_source == "Git Repo":
    st.subheader("📦 Git Repository Source")
    git_url = st.text_input("Git Repository URL")
    branch = st.text_input("Branch (optional)", value="main")
    col1, col2 = st.columns([5,1])
    with col1:
        pass
    with col2:
        if st.button("🔄", help="Clone repo"):
            with st.spinner("Cloning..."):
                try:
                    temp_dir = tempfile.mkdtemp(dir="/tmp")
                    cmd = ["git", "clone", "--depth", "1"]
                    if branch: cmd += ["--branch", branch]
                    cmd += [git_url, temp_dir]
                    subprocess.check_call(cmd)
                    st.session_state.cloned_repo_path = temp_dir
                    st.session_state.clone_status = f"📬 Cloning: {git_url}"
                except Exception as e:
                    st.session_state.clone_status = f"❌ Clone failed: {e}"
    
    st.markdown("📜 **Clone Status**")
    st.code(st.session_state.clone_status or "No repo cloned yet.")


files_to_process = []

if file_source == "Upload Files":
    uploaded_files = st.file_uploader("Upload `.pp`, `.rb`, `.yml` files", type=["pp", "rb", "yml"], accept_multiple_files=True, key="uploaded_files")
    if uploaded_files:
        files_to_process = uploaded_files

elif file_source == "Browse Existing":
    folder = st.text_input("Folder to browse", default_upload_path, key="browse_existing_path")
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder) if f.endswith(('.pp', '.rb', '.yml'))]
        selected = st.multiselect("Select files", all_files, key="browse_existing_files")
        files_to_process = [os.path.join(folder, f) for f in selected]


elif file_source == "Git Repo" and st.session_state.get("cloned_repo_path"):
    repo_root = st.session_state["cloned_repo_path"]
    full_path = repo_root

    if os.path.exists(full_path):
        # 🌿 Recursively collect subfolders as tags
        tag_folders = sorted(set(
            os.path.relpath(root, full_path)
            for root, _, _ in os.walk(full_path)
            if root != full_path
        ))

        # 🏷️ Folder tag filter (multi-select)
        selected_tags = st.multiselect("📂 Filter by Folder Tags", tag_folders, key="tag_filter")

        # 👇 Map relative path (for UI) -> full path (for processing)
        display_to_fullpath = {}
        for tag in selected_tags:
            tag_path = os.path.join(full_path, tag)
            for root, _, files in os.walk(tag_path):
                for file in files:
                    if file.endswith(('.pp', '.rb', '.yml')):
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_path, full_path)
                        display_to_fullpath[rel_path] = abs_path

        if display_to_fullpath:
            display_names = sorted(display_to_fullpath.keys())
            selected_display = st.multiselect("📄 Select files to convert", display_names, key="git_selected_files")
            files_to_process = [display_to_fullpath[name] for name in selected_display]
        else:
            st.info("No files found under selected folders.")

# === Main Processing ===
if st.button("🚀 Convert to Ansible", disabled=not files_to_process, key="convert_btn"):
    os.makedirs(summary_path, exist_ok=True)
    loading_placeholder = st.empty()
    loading_placeholder.markdown('<div class="loading-bar"></div>', unsafe_allow_html=True)

    total_files = len(files_to_process)
    progress = st.progress(0)

    for i, file in enumerate(files_to_process):
        filename = os.path.basename(file.name if hasattr(file, "name") else file)
        content = file.read().decode("utf-8") if hasattr(file, "read") else open(file, 'r').read()
        context = "Puppet module" if filename.endswith(".pp") else "Chef Recipe"

        logging.info(f"🔁 Backend: {ai.__class__.__name__} | Model: {getattr(ai, 'model_name', 'N/A')}")
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
 

# === Cleanup old cloned repos if necessary ===
def cleanup_old_clones(base_dir="cloned_repos", keep_latest=1):
    try:
        if not os.path.exists(base_dir):
            return
        all_entries = sorted(
            [(d, os.path.getmtime(os.path.join(base_dir, d))) for d in os.listdir(base_dir)],
            key=lambda x: x[1],
            reverse=True
        )
        for d, _ in all_entries[keep_latest:]:
            full_path = os.path.join(base_dir, d)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                logging.info(f"🧹 Removed old cloned repo: {full_path}")
    except Exception as e:
        logging.warning(f"Cleanup failed: {e}")

# Optional: perform cleanup on load or when switching repos
if "cloned_repo_path" in st.session_state and st.session_state.get("trigger_cleanup", False):
    cleanup_old_clones()
    st.session_state["trigger_cleanup"] = False