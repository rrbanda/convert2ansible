import logging
import argparse
import yaml
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client.types import Document

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(stream_handler)

# Load config.yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# CLI args
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--auto", help="Auto-run demo without chat", action="store_true")
parser.add_argument("-r", "--remote", help="Use remote LlamaStack server", action="store_true")
args = parser.parse_args()

# Select mode
mode = "remote" if args.remote else "local"
base_url = config["llama_stack"][mode]["base_url"]
model_id = config["llama_stack"][mode]["model"]

# Connect to server
client = LlamaStackClient(base_url=base_url)
logger.info(f"✅ Connected to Llama Stack server @ {base_url}\n")

# Create or reuse vector DB
vector_db_id = "my_documents"
vector_db_ids = [v.provider_resource_id for v in client.vector_dbs.list()]
if vector_db_id not in vector_db_ids:
    client.vector_dbs.register(
        vector_db_id=vector_db_id,
        embedding_model="all-MiniLM-L6-v2",
        embedding_dimension=384,
        provider_id="faiss"
    )

    urls = ["https://raw.githubusercontent.com/meta-llama/llama-stack/main/README.md"]
    documents = [
        Document(
            document_id=f"doc-{i}",
            content=url,
            mime_type="text/plain",
            metadata={}
        ) for i, url in enumerate(urls)
    ]

    client.tool_runtime.rag_tool.insert(
        documents=documents,
        vector_db_id=vector_db_id,
        chunk_size_in_tokens=512,
    )

# Build agent with RAG
agent = Agent(
    client,
    model=model_id,
    instructions="""
    You are a helpful assistant. Use the knowledge search tool when you need information
    from uploaded documents. Respond clearly and helpfully.
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

# Run demo prompts
if args.auto:
    prompts = [
        "Please use the knowledge search tool to tell me what you know about Llama Stack.",
        "What is the purpose of this repo?"
    ]
    session_id = agent.create_session("rag-demo-session")

    for prompt in prompts:
        logger.info(f"\n🧠 User: {prompt}")
        turn = agent.create_turn(
            messages=[{"role": "user", "content": prompt}],
            session_id=session_id,
            stream=True
        )
        for log in EventLogger().log(turn):
            log.print()
else:
    session_id = agent.create_session("rag-chat")
    while True:
        msg = input(">>> ")
        if msg.strip().lower() in ["/bye", "exit", "quit"]:
            break

        turn = agent.create_turn(
            messages=[{"role": "user", "content": msg}],
            session_id=session_id
        )
        for log in EventLogger().log(turn):
            log.print()
