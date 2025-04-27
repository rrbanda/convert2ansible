import logging
import os
import yaml
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

# === Logging config ===
try:
    os.makedirs("/tmp/logs", exist_ok=True)
    logging_path = "/tmp/logs/app.log"
except Exception:
    logging_path = "app.log"

logging.basicConfig(
    filename=logging_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === YAML flattening utility for Ansible ===
def flatten_blocks(playbook_yaml):
    """Flattens recursive `block:` nesting in Ansible playbook."""
    try:
        data = yaml.safe_load(playbook_yaml)
        for play in data:
            tasks = play.get("tasks", [])
            play["tasks"] = extract_flat_tasks(tasks)
        return yaml.dump(data, sort_keys=False)
    except Exception as e:
        logging.warning(f"Failed to flatten blocks: {e}")
        return playbook_yaml

def extract_flat_tasks(tasks):
    flat = []
    for task in tasks:
        if "block" in task:
            flat.append({k: v for k, v in task.items() if k != "block"})
            flat += extract_flat_tasks(task["block"])
        else:
            flat.append(task)
    return flat

# === AgenticModel class ===
class AgenticModel:
    def __init__(self, maas_key, maas_model, base_url="http://localhost:8321", vector_dbs=None):
        if vector_dbs is None:
            vector_dbs = ["puppet_docs", "chef_docs"]

        self.maas_key = maas_key
        self.maas_model = maas_model
        self.vector_dbs = vector_dbs

        logging.info("🔌 Initializing AgenticModel...")
        logging.info(f"📡 LlamaStack URL: {base_url}")
        logging.info(f"🧠 MaaS Model: {maas_model}")
        logging.info(f"🔐 API Key Provided: {'Yes' if bool(maas_key) else 'No'}")

        self.client = LlamaStackClient(
            base_url=base_url,
            provider_data={
                "together_api_key": self.maas_key,
                "model_id": self.maas_model
            }
        )

    def transform(self, code, mode="convert"):
        logging.info(f"📝 transform() called with mode='{mode}'")

        # === Instructions based on mode ===
        if mode == "analyze":
            instructions = """
You are an expert infrastructure automation analyst.

Your task is to analyze and explain in plain English what the input **Chef or Puppet code** does.

Be concise but precise. Focus on key resources, logic, and structure.

Avoid YAML. Do not reformat the code.

Explain what the infrastructure automation code is doing, as if to a DevOps engineer new to the codebase.
"""
        else:  # mode == "convert"
            instructions = """
You are an expert infrastructure automation assistant.

Your task is to convert input code written in **Chef or Puppet DSL** into a clean and valid **Ansible Playbook**.

Use the builtin::rag tool to retrieve and incorporate relevant examples and concepts from the provided vector databases.

You MUST follow these formatting rules:

Output only valid Ansible YAML.
Use `tasks:` under each play. Do not use `block:` unless absolutely necessary.
Avoid nested blocks. If needed, flatten them.
Use descriptive and distinct task names (e.g., "Install Apache", "Configure firewall").
Use appropriate Ansible modules (e.g., `apt`, `yum`, `copy`, `template`, `service`, `ufw`, `firewalld`, etc.).
Ensure proper indentation and correct YAML formatting.
Avoid any markdown, comments, explanations, or non-YAML content.

Do not return raw Chef or Puppet code.
Do not invent fictional modules.
Respond with YAML ONLY.
"""

        # === Dynamically create Agent instance ===
        agent = Agent(
            client=self.client,
            model="llama3.2:3b",
            instructions=instructions,
            tools=[{
                "name": "builtin::rag",
                "args": {
                    "vector_db_ids": self.vector_dbs,
                    "top_k": 3,
                    "compile": True
                }
            }],
            tool_config={"tool_choice": "auto"},
            max_infer_iters=4,
            sampling_params={
                "strategy": {"type": "top_p", "temperature": 0.3, "top_p": 0.9},
                "max_tokens": 2048
            }
        )

        try:
            session_id = agent.create_session(f"convert2ansible-{mode}")
            logging.info(f"📟 Session created: {session_id}")
            turn = agent.create_turn(
                session_id=session_id,
                messages=[{"role": "user", "content": code}],
                stream=True
            )
        except Exception as e:
            logging.error(f"❌ Failed to create session or turn: {e}")
            return "", f"ERROR: {e}"

        output = ""
        for log in EventLogger().log(turn):
            if hasattr(log, "content") and isinstance(log.content, str):
                output += log.content

        output = output.strip()

        if output:
            logging.info(f"✅ Agent completed with {len(output.split())} tokens returned.")
            return flatten_blocks(output) if mode == "convert" else output
        else:
            logging.warning("⚠️ Agent returned empty response.")
            return "", "⚠️ No response from agent"
