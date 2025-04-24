# test/test_dsl_classifier.py

from tools.dsl_classifier_tool import dsl_classifier_tool

def test_chef_classification():
    chef_code = "cookbook_file '/etc/motd' do\n  source 'motd'\nend"
    result = dsl_classifier_tool(chef_code)
    print(f"[TEST] Chef Classification: {result}")
    assert result == "chef"

def test_puppet_classification():
    puppet_code = "class apache {\n  package { 'httpd': ensure => installed }\n}"
    result = dsl_classifier_tool(puppet_code)
    print(f"[TEST] Puppet Classification: {result}")
    assert result == "puppet"

def test_unknown_classification():
    unknown_code = "print('Hello world')"
    result = dsl_classifier_tool(unknown_code)
    print(f"[TEST] Unknown Classification: {result}")
    assert result == "unknown"

if __name__ == "__main__":
    test_chef_classification()
    test_puppet_classification()
    test_unknown_classification()
    print("✅ All dsl_classifier_tool tests passed.")
