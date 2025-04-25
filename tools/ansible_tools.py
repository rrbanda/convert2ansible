# tools/ansible_tools.py

from llama_stack_client.lib.agents.client_tool import client_tool
import subprocess
import os
import json

@client_tool
def lint_playbook(filepath: str, profile: str = "basic", fix: bool = False, format: str = "json") -> dict:
    """
    Run ansible-lint on a given playbook with optional profile, fix, and format.

    :param filepath: Path to the playbook YAML file
    :param profile: Linting profile to use (min, basic, safety, production, etc.)
    :param fix: Whether to apply fixes if possible
    :param format: Output format ('json', 'codeclimate', 'sarif', etc.)
    :returns: A structured dict with linting results
    """

    if not os.path.exists(filepath):
        return {
            "status": "error",
            "message": f"❌ File not found: {filepath}",
            "errors": [],
            "warnings": []
        }

    command = ["ansible-lint", filepath, "--profile", profile, "--format", format]
    if fix:
        command.append("--fix")

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip()

        # Try to parse JSON output if format is JSON or compatible
        if format in {"json", "sarif", "codeclimate"}:
            try:
                parsed = json.loads(output)
                return {
                    "status": "success" if result.returncode == 0 else "warning",
                    "message": "✅ No issues found." if result.returncode == 0 else "⚠️ Lint issues detected.",
                    "output": parsed
                }
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "❌ Failed to parse lint output.",
                    "errors": [],
                    "raw_output": output
                }

        # Fallback for other formats
        return {
            "status": "success" if result.returncode == 0 else "warning",
            "message": output
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Lint failed: {str(e)}",
            "errors": [],
            "warnings": []
        }
