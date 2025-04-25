from tools.ansible_tools import lint_playbook
from llama_stack_client import LlamaStackClient, Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

# Connect to Llama Stack
client = LlamaStackClient(base_url="http://localhost:8321")

# Build the agent with tool function
agent = Agent(
    client=client,
    model="llama3.2:3b",
    instructions="""
You are an Ansible playbook quality checker.
Always call lint_playbook on the provided file path and return only the result.
""",
    tools=[lint_playbook],  # 🧠 Pass tool function, not string
    max_infer_iters=3
)

# Run session
session_id = agent.create_session("lint-session")
turn = agent.create_turn(
    session_id=session_id,
    messages=[{"role": "user", "content": "Please lint this file: samples/apache.yml"}],
    stream=True
)

for log in EventLogger().log(turn):
    log.print()
