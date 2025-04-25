import logging
import os
import yaml
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

# Logging config
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

def flatten_blocks(playbook_yaml):
    """Flattens recursive `block:` nesting in Ansible playbook."""
    try:
        data = yaml.safe_load(playbook_yaml)
        for play in data:
            tasks = play.get("tasks", [])
            play["tasks"] = extract_flat_tasks(tasks)
        return yaml.dump(data, sort_keys=False)
    except Exception as e:
        logging.warning(f"❌ Failed to flatten blocks: {e}")
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

class AgenticModel:
    def __init__(self, maas_key, maas_model, base_url="http://localhost:8321", vector_dbs=["puppet_docs", "chef_docs"]):
        self.maas_key = maas_key
        self.maas_model = maas_model
        self.vector_dbs = vector_dbs

        logging.info("🔌 Initializing AgenticModel...")
        logging.info(f"Using LlamaStack @ {base_url}")
        logging.info(f"Using MaaS model: {maas_model} with API key set: {'yes' if bool(maas_key) else 'no'}")

        self.client = LlamaStackClient(
            base_url=base_url,
            provider_data={
                "together_api_key": self.maas_key,
                "model_id": self.maas_model  # ✅ Tells server to use this for generation
            }
        )

        self.agent = Agent(
            client=self.client,
            model="llama3.2:3b",  # LlamaStack local model for orchestration
            instructions="""
You are a DevOps expert. Convert the given Chef or Puppet infrastructure code into a valid Ansible playbook.
Use the builtin::rag tool to enrich your context with real-world infrastructure knowledge before responding.

❌ Avoid nesting `block:` inside another `block:` unless strictly required.
✅ Prefer flat task lists.
✅ Do NOT repeat or duplicate task names or structure.
✅ Output only clean and minimal YAML without recursion.

Respond with only valid Ansible YAML. No markdown, no comments.
            """,
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

        logging.info("Agent initialized with RAG and remote model override.")

    def transform(self, code, context=""):
        logging.info(f"📝 Invoking Agent with DSL input. Context: {context}")
        session_id = self.agent.create_session("convert2ansible")
        logging.info(f"📡 Agent session started: {session_id}")

        turn = self.agent.create_turn(
            session_id=session_id,
            messages=[{"role": "user", "content": code}],
            stream=True
        )

        final_output = ""
        for log in EventLogger().log(turn):
            if hasattr(log, "content") and isinstance(log.content, str):
                final_output += log.content

        final_output = final_output.strip()
        if final_output:
            logging.info("Agent response successfully received.")
            final_output = flatten_blocks(final_output)
        else:
            logging.warning("⚠️ Agent returned no output.")

        return final_output
