import requests
import json
import logging

class MaasModel:
    def __init__(self, api_key, endpoint_url, model_name, stream=False):
        self.api_key = api_key
        self.model_name = model_name
        self.stream = stream

        # Ensure /v1/completions path
        if not endpoint_url.rstrip("/").endswith("/v1"):
            endpoint_url = endpoint_url.rstrip("/") + "/v1"
        self.endpoint_url = endpoint_url + "/completions"

    def transform(self, code, context, stream_ui=False):
        prompt = f"""As a software developer, convert this {context} to an Ansible Playbook.
Only provide the YAML code (no explanations, no comments). Use proper indentation and formatting.

[INPUT]
{code}
[OUTPUT]
"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": 2048,
            "temperature": 0.2,
            "stream": self.stream
        }

        try:
            logging.info(f"[MaaS] POST {self.endpoint_url} | Model: {self.model_name} | Stream: {self.stream}")
            response = requests.post(self.endpoint_url, headers=headers, json=payload, stream=self.stream)
            response.raise_for_status()

            if self.stream:
                result = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8").replace("data: ", "")
                        if line_str.strip() == "[DONE]":
                            break
                        try:
                            json_obj = json.loads(line_str)
                            if "choices" in json_obj and json_obj["choices"]:
                                chunk = json_obj["choices"][0]["text"]
                                result += chunk
                                if stream_ui:
                                    yield chunk  # 👈 Stream to UI
                        except json.JSONDecodeError as err:
                            logging.warning(f"[MaaS] JSON decode error: {err}")
                if not stream_ui:
                    yield result
            else:
                result = response.json()
                logging.debug(f"[MaaS] Raw response: {result}")
                choices = result.get("choices")
                if not choices or not isinstance(choices, list) or not choices[0].get("text"):
                    logging.error(f"[MaaS] Unexpected response structure: {result}")
                    yield "MaaS response did not contain valid 'choices'."
                else:
                    yield choices[0]["text"]

        except Exception as e:
            logging.exception("[MaaS] Error during prompt generation")
            yield f"Error contacting MaaS: {e}"
