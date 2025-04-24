# tools/convert2ansible_agent.py

import argparse
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from tools.dsl_classifier_tool import dsl_classifier_tool

# ----------------------------------
# CLI Arguments
# ----------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--input-file", required=True, help="Path to DSL input file (Chef or Puppet)")
args = parser.parse_args()

with open(args.input_file, "r") as f:
    INPUT_CODE = f.read()

# ----------------------------------
# Classify DSL
# ----------------------------------
dsl_type = dsl_classifier_tool(INPUT_CODE)
if dsl_type not in ["chef", "puppet"]:
    print(f"❌ DSL classified as: {dsl_type}. Only 'chef' and 'puppet' are supported.")
    exit(1)

print(f"🧠 DSL classified as: {dsl_type}")

# ----------------------------------
# Connect to Llama Stack
# ----------------------------------
client = LlamaStackClient(base_url="http://localhost:8321")
print("✅ Connected to Llama Stack server")

# ----------------------------------
# Select vector DB
# ----------------------------------
vector_db_id = f"{dsl_type}_docs"
available_dbs = [v.provider_resource_id for v in client.vector_dbs.list()]
if vector_db_id not in available_dbs:
    print(f"❌ Vector DB '{vector_db_id}' not found. Please run `tools/rag_loader.py` first.")
    exit(1)

# ----------------------------------
# Build Agent
# ----------------------------------
agent = Agent(
    client=client,
    model="llama3.2:3b",
    instructions=f"""
    You are an AI assistant helping users convert {dsl_type} DSL code into Ansible playbooks.
    Use helpful context retrieved via RAG and output clean, working Ansible YAML only.
    """,
    tools=[{
        "name": "builtin::rag",
        "args": {
            "vector_db_ids": [vector_db_id],
            "top_k": 1
        }
    }],
    tool_config={"tool_choice": "auto"}
)

# ----------------------------------
# Convert DSL to Ansible
# ----------------------------------
session_id = agent.create_session("convert2ansible")
print(f"\n🧠 Sending code to agent for {dsl_type} → Ansible conversion...")

turn = agent.create_turn(
    messages=[{"role": "user", "content": INPUT_CODE}],
    session_id=session_id,
    stream=True
)

for log in EventLogger().log(turn):
    log.print()
