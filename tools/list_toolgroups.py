from llama_stack_client import LlamaStackClient

client = LlamaStackClient()
toolgroups = [tg.toolgroup_id for tg in client.tools.list()]
print("Available toolgroups:", toolgroups)
