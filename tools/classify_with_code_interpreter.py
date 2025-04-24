# tools/classify_with_code_interpreter.py

import argparse
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

# ------------------------------
# CLI Argument
# ------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--input-file", required=True, help="Path to DSL input file (Chef or Puppet)")
args = parser.parse_args()

with open(args.input_file, "r") as f:
    input_code = f.read()

# ------------------------------
# Connect to Llama Stack
# ------------------------------
client = LlamaStackClient(base_url="http://localhost:8321")
print("✅ Connected to Llama Stack")

# ------------------------------
# Build Code-Interpreter Agent
# ------------------------------
agent = Agent(
    client=client,
    model="llama3.2:3b",
    instructions="""
    You are a Python DSL classifier. You will receive Python code defining a function `dsl_classifier_tool`,
    along with some DSL code to classify. Use the builtin::code_interpreter tool to evaluate it and return 'chef', 'puppet', or 'unknown'.
    """,
    tools=["builtin::code_interpreter"],
    tool_config={"tool_choice": "auto"}
)

# ------------------------------
# Construct Prompt to Trigger Tool
# ------------------------------
python_code = f"""
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
dsl_classifier_tool(code)
"""

# ------------------------------
# Run Classification Agent
# ------------------------------
session_id = agent.create_session("code-interpreter-classifier")
print("🧠 Sending code for classification using code_interpreter...")

turn = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": python_code}],
    stream=True
)

for log in EventLogger().log(turn):
    log.print()
