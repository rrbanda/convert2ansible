# tools/register_ansible_tools.py
from llama_stack_client import LlamaStackClient
from llama_stack_client.toolgroups import ToolGroup  # ✅ Correct path
from tools import ansible_tools  # this triggers the @client_tool registration

client = LlamaStackClient(base_url="http://localhost:8321")

ToolGroup.register(
    client=client,
    toolgroup_id="custom::ansible_tools",
    provider_id="client-tools",  # required in latest versions
    name="Ansible Tools",
    description="Custom tools for linting and validation"
)

print("✅ Tool registration completed.")
