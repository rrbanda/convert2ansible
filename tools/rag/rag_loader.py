# tools/rag_loader.py

from llama_stack_client import LlamaStackClient
from llama_stack_client.types import Document

client = LlamaStackClient(base_url="http://localhost:8321")
print(" Connected to Llama Stack")

# DSL guidance content (could also be loaded from external files)
chef_content = """
Chef is a Ruby-based configuration management tool. 
Resources like `cookbook_file`, `template`, `package`, and `service` define system state.
Attributes are accessed using node['attribute'].
You should convert Chef logic into Ansible tasks using modules like `copy`, `template`, `apt`, `yum`, and `service`.
"""

puppet_content = """
Puppet uses a declarative DSL for defining system configuration. 
Classes and resources are defined using `class`, `package {}`, and `file {}` syntax.
Variables use `$`, and the format is key => value.
Convert Puppet resources to Ansible modules like `package`, `file`, `copy`, and `template`.
"""

# Prepare vector DBs
dbs = {
    "chef_docs": chef_content,
    "puppet_docs": puppet_content
}

for vector_db_id, content in dbs.items():
    existing = [v.provider_resource_id for v in client.vector_dbs.list()]
    if vector_db_id not in existing:
        client.vector_dbs.register(
            vector_db_id=vector_db_id,
            embedding_model="all-MiniLM-L6-v2",
            embedding_dimension=384,
            provider_id="faiss"
        )
        print(f"📚 Created vector DB: {vector_db_id}")

        doc = Document(
            document_id=f"{vector_db_id}-guidance",
            content=content,
            mime_type="text/plain",
            metadata={}
        )

        client.tool_runtime.rag_tool.insert(
            documents=[doc],
            vector_db_id=vector_db_id,
            chunk_size_in_tokens=512
        )
        print(f"📥 Ingested guidance into {vector_db_id}")
    else:
        print(f"ℹ️  {vector_db_id} already exists")

print(" RAG vector DBs ready for classification pipeline.")
