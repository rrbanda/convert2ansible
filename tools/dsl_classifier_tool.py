# tools/dsl_classifier_tool.py

def dsl_classifier_tool(code: str) -> str:
    """
    Classifies the given DSL code as 'chef', 'puppet', or 'unknown'.
    """
    chef_keywords = ["recipe", "::", "default['", "cookbook_file", "template", "node["]
    puppet_keywords = ["class ", "define ", "$", "notify", "file {", "package {"]

    code_lower = code.lower()

    if any(k in code_lower for k in chef_keywords):
        return "chef"
    elif any(k in code_lower for k in puppet_keywords):
        return "puppet"
    else:
        return "unknown"
