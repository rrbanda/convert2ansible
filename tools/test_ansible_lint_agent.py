# tools/test_ansible_lint_agent.py
import argparse
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True, help="Ansible playbook to lint")
args = parser.parse_args()

client = LlamaStackClient(base_url="http://localhost:8321")

agent = Agent(
    client=client,
    model="llama3.2:3b",  # Local model for inference; not used in tool call
    instructions="You are an Ansible linter. Use the ansible_lint_check tool.",
    tools=["custom::ansible_tools/ansible_lint_check"],
    tool_config={"tool_choice": "auto"}
)

session_id = agent.create_session("ansible-lint-test")

turn = agent.create_turn(
    session_id=session_id,
    messages=[{
        "role": "user",
        "content": f"Run ansible_lint_check on {args.file}"
    }],
    stream=True
)

for log in EventLogger().log(turn):
    log.print()
