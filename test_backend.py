import logging
from ai_modules.ollama_explanator import Ollama
from ai_modules.maas_model import MaasModel
from ai_modules.wxai import WxAI

logging.basicConfig(level=logging.INFO)

# Sample input to simulate a real file
sample_puppet_code = """
package { 'nginx':
  ensure => installed,
}

service { 'nginx':
  ensure => running,
  enable => true,
}
"""

def run_backend(name, backend):
    print(f"\n--- Testing: {name} ---")
    try:
        output = backend.transform(sample_puppet_code, "Puppet module")
        print(f"✅ Output from {name}:\n{output[:500]}...\n")
    except Exception as e:
        print(f"❌ Error from {name}: {e}\n")

if __name__ == "__main__":
    # Test Ollama (if local Ollama running)
    ollama = Ollama(model_name="deepseek-r1:8b", host="localhost:11434")
    run_backend("Ollama", ollama)

    # Test WxAI (dummy placeholder)
    wxai = WxAI()
    run_backend("WxAI", wxai)

    # Test MaaS (use your real values or env vars)
    maas = MaasModel(
        api_key="xyz",  # 🔁 Replace with a valid token
        endpoint_url="https://granite-8b-code-instruct-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443",
        model_name="granite-8b-code-instruct-128k",
        stream=False
    )
    run_backend("MaaS", maas)
