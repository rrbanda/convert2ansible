# Setup, Logging, Sidebar Logo Injection

import os
import re
import shutil
import tempfile
import subprocess
import logging
import urllib.parse
from time import time
from configparser import ConfigParser

import streamlit as st
import streamlit.components.v1 as components

# === Logging ===
try:
    os.makedirs("/tmp/logs", exist_ok=True)
    logging_path = "/tmp/logs/app.log"
except Exception:
    logging_path = "app.log"

logging.basicConfig(
    filename=logging_path,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# === Streamlit Page Setup ===
st.set_page_config(page_title="Convert IaC to Ansible", page_icon="🅰️", layout="wide")

# === Inject Ansible Logo ABOVE Sidebar ===
st.markdown("""
<style>
[data-testid="stSidebarNav"]::before {
    content: "";
    display: block;
    margin: 0 auto 16px auto;
    background-image: url('https://github.com/ansible/logos/blob/main/community-usage/correct-use-white.png?raw=true');
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
    height: 100px;
}
</style>
""", unsafe_allow_html=True)

# === Config File ===
config = ConfigParser()
config.read("settings.config")
default_upload_path = config.get("files", "file_location", fallback="uploads")
default_output_path = config.get("files", "summary_location", fallback="results")
# app.py — Part 2 of N: Sidebar + Backend Selector

st.sidebar.title("⚙️ Settings")

ai_choice = st.sidebar.radio("Choose Backend", ["maas", "agentic"], index=0)

if ai_choice == "maas":
    from ai_modules.maas_model import MaasModel
    st.sidebar.markdown("### 🔐 MaaS Settings")
    maas_key = st.sidebar.text_input("API Key", type="password")
    maas_url = st.sidebar.text_input("Endpoint URL", value="https://mixtral-8x7b-instruct-v0-1-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443")
    maas_model = st.sidebar.text_input("Model Name", value="mistralai/Mixtral-8x7B-Instruct-v0.1")
    maas_stream = st.sidebar.checkbox("Enable Streaming", value=False)
    if maas_key and maas_url and maas_model:
        ai = MaasModel(api_key=maas_key, endpoint_url=maas_url, model_name=maas_model, stream=maas_stream)
    else:
        st.stop()

elif ai_choice == "agentic":
    from ai_modules.agentic_model import AgenticModel
    st.sidebar.markdown("### 🧠 Agentic Settings")
    maas_key = st.sidebar.text_input("MaaS API Key", type="password")
    maas_model = st.sidebar.text_input("Remote Model ID", value="mistralai/Mixtral-8x7B-Instruct-v0.1")
    base_url = st.sidebar.text_input("LlamaStack Server URL", value="http://localhost:8321")
    if maas_key and maas_model and base_url:
        ai = AgenticModel(maas_key=maas_key, maas_model=maas_model, base_url=base_url)
    else:
        st.stop()

# Output path for results
summary_path = st.sidebar.text_input("📂 Output Folder", default_output_path)
# app.py — Part 3 of N: File Input & Selection

# === Init session state ===
for key, default in {
    "clone_status": "",
    "cloned_repo_path": "",
    "selected_git_folder": "",
    "git_files": [],
    "selected_files": [],
    "available_tags": [],
    "filter_tags": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# === File source selector ===
file_source = st.radio("📁 Choose File Source", ["Upload Files", "Browse Existing", "Git Repo"])
files_to_process = []

if file_source == "Upload Files":
    uploaded_files = st.file_uploader(
        "Upload `.pp`, `.rb`, or `.yml` files",
        type=["pp", "rb", "yml"],
        accept_multiple_files=True
    )
    if uploaded_files:
        files_to_process = uploaded_files

elif file_source == "Browse Existing":
    folder = st.text_input("📂 Folder to browse", default_upload_path)
    if os.path.exists(folder):
        all_files = [f for f in os.listdir(folder) if f.endswith(('.pp', '.rb', '.yml'))]
        selected = st.multiselect("📄 Select files", all_files)
        files_to_process = [os.path.join(folder, f) for f in selected]

elif file_source == "Git Repo":
    st.subheader("🔗 Clone Git Repository")
    git_url = st.text_input("Git Repository URL")
    branch = st.text_input("Branch (optional)", value="main")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Clone"):
            with st.spinner("Cloning..."):
                try:
                    temp_dir = tempfile.mkdtemp(dir="/tmp")
                    cmd = ["git", "clone", "--depth", "1"]
                    if branch: cmd += ["--branch", branch]
                    cmd += [git_url, temp_dir]
                    subprocess.check_call(cmd)
                    st.session_state.cloned_repo_path = temp_dir
                    st.session_state.clone_status = f"✅ Cloned: {git_url}"
                except Exception as e:
                    st.session_state.clone_status = f"❌ Clone failed: {e}"

    st.code(st.session_state.clone_status or "No repo cloned yet.")

    repo_root = st.session_state.cloned_repo_path
    if os.path.exists(repo_root):
        tag_folders = sorted(set(
            os.path.relpath(root, repo_root)
            for root, _, _ in os.walk(repo_root)
            if root != repo_root
        ))

        selected_tags = st.multiselect("🏷️ Filter by Folders", tag_folders)
        display_to_fullpath = {}

        for tag in selected_tags:
            tag_path = os.path.join(repo_root, tag)
            for root, _, files in os.walk(tag_path):
                for file in files:
                    if file.endswith(('.pp', '.rb', '.yml')):
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(abs_path, repo_root)
                        display_to_fullpath[rel_path] = abs_path

        if display_to_fullpath:
            display_names = sorted(display_to_fullpath.keys())
            selected_display = st.multiselect("📄 Select files to convert", display_names)
            files_to_process = [display_to_fullpath[name] for name in selected_display]
        else:
            st.info("No matching files found in selected folders.")
# app.py — Part 4 of N: Analyze & Convert

# === Store results by filename ===
file_outputs = {}  # format: { "file.pp": {"analysis": ..., "yaml": ...} }

# === Step 1: Analyze Files ===
st.markdown("### 🧠 Step 1: Analyze Code")
st.caption("Get a human-readable explanation of the code logic before converting it.")

if st.button("🔍 Analyze Files", disabled=not files_to_process, key="analyze_btn"):
    os.makedirs(summary_path, exist_ok=True)
    progress = st.progress(0)

    for i, file in enumerate(files_to_process):
        filename = os.path.basename(file.name if hasattr(file, "name") else file)
        content = file.read().decode("utf-8") if hasattr(file, "read") else open(file, 'r').read()
        context = "Puppet module" if filename.endswith(".pp") else "Chef Recipe"

        logging.info(f"🔍 Analyzing: {filename}")
        try:
            with st.spinner(f"Analyzing {filename}..."):
                start = time()
                analysis = ai.transform(content, mode="analyze")
                duration = time() - start

            file_outputs.setdefault(filename, {})["analysis"] = analysis.strip()
            st.success(f"✅ {filename} analyzed in {duration:.1f}s")

        except Exception as e:
            st.error(f"❌ Error analyzing {filename}: {e}")
            logging.exception(f"Exception while analyzing {filename}")

        progress.progress((i + 1) / len(files_to_process))


# === Step 2: Convert to Ansible ===
st.markdown("### 🛠️ Step 2: Convert to Ansible")
st.caption("Generate valid Ansible playbooks from the input DSL code.")

if st.button("🚀 Convert to Ansible", disabled=not files_to_process, key="convert_btn"):
    os.makedirs(summary_path, exist_ok=True)
    progress = st.progress(0)

    for i, file in enumerate(files_to_process):
        filename = os.path.basename(file.name if hasattr(file, "name") else file)
        content = file.read().decode("utf-8") if hasattr(file, "read") else open(file, 'r').read()
        context = "Puppet module" if filename.endswith(".pp") else "Chef Recipe"

        logging.info(f"🛠️ Converting: {filename}")
        try:
            with st.spinner(f"Converting {filename}..."):
                start = time()
                output = ai.transform(content, mode="convert")
                duration = time() - start

            # Extract just the YAML if inside ```yaml codeblock
            match = re.search(r"```yaml\n(.*?)\n```", output, re.DOTALL)
            yaml_text = match.group(1) if match else output.strip()

            # Store result
            file_outputs.setdefault(filename, {})["yaml"] = yaml_text

            # Save YAML to disk
            result_path = os.path.join(summary_path, f"{filename}.yaml")
            with open(result_path, "w") as f:
                f.write(yaml_text)

            st.success(f"✅ {filename} converted in {duration:.1f}s")

        except Exception as e:
            st.error(f"❌ Error converting {filename}: {e}")
            logging.exception(f"Exception while converting {filename}")

        progress.progress((i + 1) / len(files_to_process))
# app.py — Part 5 of N: Final Result Viewer

st.markdown("---")
st.markdown("## 📤 Results")

if not file_outputs:
    st.info("No output to show yet. Please Analyze or Convert files above.")

for filename, result in file_outputs.items():
    st.markdown(f"### 📄 {filename}")

    # === Analysis Block ===
    if "analysis" in result:
        with st.expander("🧠 Analysis Summary", expanded=False):
            st.markdown(result["analysis"])
    else:
        st.markdown("_No analysis available._")

    # === YAML Playbook Block ===
    if "yaml" in result:
        with st.expander("📜 Ansible Playbook", expanded=False):
            yaml_text = result["yaml"]
            unique_id = f"code_{filename.replace('.', '_')}"
            encoded = urllib.parse.quote(yaml_text)

            # Action buttons: Copy / Download
            st.markdown(f"""
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
            """, unsafe_allow_html=True)

            # YAML viewer
            components.html(f"""
                <div id="{unique_id}"
                     style="max-height: 400px; overflow-y: auto; border: 1px solid #555; border-radius: 8px; padding: 10px; background-color: #1e1e1e; color: white; font-family: monospace; font-size: 14px;">
                    <pre style="margin: 0;">{yaml_text}</pre>
                </div>
            """, height=450)
    else:
        st.markdown("_No playbook generated yet._")
