# tools/register_dsl_classifier.py

from llama_stack_client import LlamaStackClient
from tools.dsl_classifier_tool import dsl_classifier_tool

client = LlamaStackClient(base_url="http://localhost:8321")

client.tools.register_function(
    name="dsl_classifier_tool",
    description="Classifies DSL code as Chef, Puppet, or Unknown.",
    parameters={"code": "The DSL code string to classify"},
    implementation=dsl_classifier_tool
)

print("✅ dsl_classifier_tool registered successfully.")
