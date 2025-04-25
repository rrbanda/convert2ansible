import argparse
import yaml
import os
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

# ------------------------------
# CLI Arguments
# ------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--input-file", required=True, help="Path to input DSL code (Chef or Puppet)")
parser.add_argument("--remote", action="store_true", help="Use remote MaaS backend for conversion")
args = parser.parse_args()

# ------------------------------
# Load DSL Code
# ------------------------------
with open(args.input_file, "r") as f:
    input_code = f.read()

# ------------------------------
# Load Config
# ------------------------------
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ------------------------------
# Classifier Setup (local by default)
# ------------------------------
classifier_env = config.get("default", "local")
ollama_cfg = config["llama_stack"][classifier_env]
classifier_model = ollama_cfg["model"]
classifier_client = LlamaStackClient(base_url=ollama_cfg["base_url"])

print(f"✅ Connected to Llama Stack server @ {ollama_cfg['base_url']}")
print("🔎 Classifying DSL using builtin::code_interpreter...")

classifier_agent = Agent(
    client=classifier_client,
    model=classifier_model,
    instructions="""
You are a Python interpreter. Evaluate the function dsl_classifier_tool
and print only one word — either 'chef', 'puppet', or 'unknown'.
    """,
    tools=["builtin::code_interpreter"],
    tool_config={"tool_choice": "auto"}
)

classifier_code = f"""
def dsl_classifier_tool(code):
    chef_keywords = ["recipe", "::", "default['", "cookbook_file", "template", "node["]
    puppet_keywords = ["class ", "define ", "$", "notify", "file {{", "package {{"]
    code_lower = code.lower()
    if any(k in code_lower for k in chef_keywords):
        return "chef"
    elif any(k in code_lower for k in puppet_keywords):
        return "puppet"
    else:
        return "unknown"

code = \"\"\"{input_code}\"\"\"
print(dsl_classifier_tool(code))
"""

dsl_type = None
session_id = classifier_agent.create_session("dsl-classifier")
turn = classifier_agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": classifier_code}],
    stream=True
)

# Parse classifier output
for log in EventLogger().log(turn):
    if hasattr(log, "content") and isinstance(log.content, str):
        output = log.content.strip().lower()
        print(f"🔎 Raw classifier output: {output}")
        if output in ["chef", "puppet"]:
            dsl_type = output
            break

if not dsl_type:
    print("❌ Failed to classify DSL.")
    exit(1)

print(f"\n🧠 DSL classified as: {dsl_type}")

# ------------------------------
# Conversion Agent Setup
# ------------------------------
if args.remote:
    maas_cfg = config["llama_stack"]["maas"]
    conversion_model = maas_cfg["model"]
    api_key = maas_cfg["api_key"]
    conversion_client = LlamaStackClient(
        base_url=maas_cfg["base_url"],
        headers={"X-LlamaStack-Provider-Data": f'{{ "together_api_key": "{api_key}" }}'}
    )
else:
    conversion_model = ollama_cfg["model"]
    conversion_client = classifier_client

print(f"\n🛠️ Converting {dsl_type} to Ansible using builtin::rag...")

agent = Agent(
    client=conversion_client,
    model=conversion_model,
    instructions=f"""
You are a DevOps expert. Convert {dsl_type} infrastructure code to a valid Ansible playbook.
Use the builtin::rag tool to retrieve helpful examples. Respond with ONLY valid YAML.
No markdown, no explanations, no comments — just clean Ansible playbook.
    """,
    tools=[{
        "name": "builtin::rag",
        "args": {
            "vector_db_ids": [f"{dsl_type}_docs"],
            "top_k": 3
        }
    }],
    tool_config={"tool_choice": "auto"},
    input_shields=[],
    output_shields=[],
    max_infer_iters=4,
    sampling_params={
        "strategy": {"type": "top_p", "temperature": 0.3, "top_p": 0.9},
        "max_tokens": 2048
    }
)

session_id = agent.create_session(f"{dsl_type}-to-ansible")
turn = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": input_code}],
    stream=True
)

# Collect and print response
final_output = ""
for log in EventLogger().log(turn):
    if hasattr(log, "content") and isinstance(log.content, str):
        final_output += log.content

final_output = final_output.strip()
if final_output:
    print("\n✅ Final Ansible Playbook:\n")
    print(final_output)
else:
    print("⚠️ No assistant output detected. Check agent or RAG behavior.")