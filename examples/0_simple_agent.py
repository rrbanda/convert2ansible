import logging
import argparse
import yaml
from termcolor import cprint
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

# ----------------------------------
# Logging setup
# ----------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(stream_handler)

# ----------------------------------
# Load config.yaml
# ----------------------------------
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ----------------------------------
# Command-line arguments
# ----------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--auto", help="Run demo prompts automatically", action="store_true")
parser.add_argument("-s", "--session-info-on-exit", help="Print session info on exit", action="store_true")
parser.add_argument("-r", "--remote", help="Use remote LlamaStack server from config.yaml", action="store_true")
args = parser.parse_args()

mode = "remote" if args.remote else "local"
base_url = config["llama_stack"][mode]["base_url"]
model_id = config["llama_stack"][mode]["model"]

# ----------------------------------
# Connect to LlamaStack
# ----------------------------------
client = LlamaStackClient(base_url=base_url)
logger.info(f"✅ Connected to Llama Stack server @ {base_url}\n")

# ----------------------------------
# Agent Definition
# ----------------------------------
agent = Agent(
    client=client,
    model=model_id,
    instructions="""
    You are a helpful assistant. You can use built-in tools like RAG and web search
    to answer user questions with context and depth.
    """,
    tools=[
        "builtin::rag",
        "builtin::websearch"
    ],
    tool_config={"tool_choice": "auto"}
)

# ----------------------------------
# Auto Mode (non-interactive)
# ----------------------------------
if args.auto:
    prompts = [
        "What is Retrieval Augmented Generation?",
        "Search the web for the latest Python release."
    ]
    session_id = agent.create_session(session_name="demo-session")

    for prompt in prompts:
        logger.info(f"\n🧠 User: {prompt}")
        turn = agent.create_turn(
            messages=[{"role": "user", "content": prompt}],
            session_id=session_id,
            stream=True
        )
        for log in EventLogger().log(turn):
            log.print()

# ----------------------------------
# Chat Mode (interactive)
# ----------------------------------
else:
    session_id = agent.create_session(session_name="interactive-chat")
    while True:
        user_input = input(">>> ")
        if user_input.strip().lower() in ["/bye", "exit", "quit"]:
            if args.session_info_on_exit:
                session = client.agents.session.retrieve(session_id=session_id, agent_id=agent.agent_id)
                print(session.to_dict())
            break

        turn = agent.create_turn(
            messages=[{"role": "user", "content": user_input}],
            session_id=session_id
        )

        for log in EventLogger().log(turn):
            log.print()
