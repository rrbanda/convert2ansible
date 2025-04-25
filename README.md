# 🧙‍♂️ Convert to Ansible
Convert to Ansible is a smart, expandable Python-based tool that converts [Puppet](https://www.puppet.com) modules or [Chef](https://www.chef.io) recipes into clean, production-grade [Ansible](https://docs.ansible.com) playbooks using Gen AI.

It supports:
- ✅ **Local Ollama** for offline inference
- ✅ **MaaS (Model-as-a-Service)** with `granite-8b-code-instruct-128k` for enterprise-grade generation
- ✅ **Agentic mode with RAG**: combines local **LlamaStack** RAG with remote **MaaS** for high-quality playbooks

---

### 📐 High level Architecture

```text
                        +-------------------+
                        |   User Interface  |
                        | (Streamlit UI App)|
                        +---------+---------+
                                  |
                                  v
                +-----------------------------+
                |       Backend Selector      |
                |  [ollama | maas | agentic]  |
                +--------+----------+---------+
                         |          |
            +------------+          +---------------------+
            |                                     |
   +--------v--------+                   +--------v--------+
   | Ollama Runtime  |                   |  Agentic Backend |
   | (local LLMs)    |                   | using LlamaStack |
   +-----------------+                   +--------+--------+
                                                 |
                                                 v
         +------------------- RAG + MaaS Agent Pipeline --------------------+
         |                                                                  |
         |  LlamaStack Agent (local)                                        |
         |  └── uses builtin::rag + embeddings (MiniLM, Ollama, etc.)       |
         |                                                                  |
         |  Generation handled by → Granite 8B Code Instruct via MaaS       |
         +------------------------------------------------------------------+
```

---

### 🚀 How to Use

Tested with Python 3.11+

#### 1. Clone the repo
```bash
git clone https://github.com/bpaskin/Automation-Code-SorcererX.git
cd Automation-Code-SorcererX
```

#### 2. Setup a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Edit configuration files
- `settings.config` for general paths and default backend
- `config.yaml` for model settings (Ollama, LlamaStack, MaaS)

Example `config.yaml`:

```yaml
default: local

llama_stack:
  local:
    base_url: http://localhost:8321
    model: llama3.2:3b

  maas:
    base_url: https://granite-8b-code-instruct-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com/v1
    model: granite-8b-code-instruct-128k
    api_key: "YOUR_MAAS_API_KEY"
```

---

### 💻 Launch the App (Streamlit UI)

```bash
streamlit run app.py
```

#### Features:
- Upload or browse code files (`.pp`, `.rb`, `.yml`)
- Convert using **Ollama**, **MaaS**, or the **Agentic RAG+MaaS** pipeline
- Output clean Ansible playbooks
- Git repo integration with tag filtering
- Linting (optional extension)

---

### 📂 Project Structure

```text
├── app.py                    # Streamlit UI
├── ai_modules/
│   ├── ollama_explanator.py
│   ├── maas_model.py
│   └── agentic_model.py     # Agentic backend using LlamaStack + MaaS
├── tools/
│   └── convert2ansible_agent.py
├── config.yaml
├── settings.config
├── uploads/
├── results/
```

---

### 🧠 VectorDB Requirements (Agentic mode)
Ensure your LlamaStack server has these vector DBs created:

- `puppet_docs`
- `chef_docs`

You can preload sample content via the LlamaStack admin or your own ingest script.

---

### 🤝 Contributions

Pull requests, issues, and feature suggestions are welcome!

---

⚠️ Disclaimer

   Convert to Ansible is a fun project created for experimenting with the tech stack and evaluating the responses . 
   It is not officially supported by any enterprise.

---
