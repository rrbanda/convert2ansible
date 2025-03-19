from .explanator import Explanator
from ollama import generate, Client
from fileio.settings import Settings

# Assisted by WCA@IBM
# Latest GenAI contribution: ibm/granite-8b-code-instruct
'''
This code defines a class called Ollama which inherits from the Explanator class. The __init__ method initializes the class with a model_name and code_data. The who_am_i and greet methods are inherited from the Explanator class and simply call their respective methods. The generate_explanation method generates an explanation for the provided code_data using the generate function from the model_name.
'''
class Ollama(Explanator):
    def __init__(self):
        settings = Settings()
        ollama_settings = settings.read_sections("settings.config", "ollama")
        ollama_model = settings.getSettingValue(ollama_settings, "model_name")
        ollama_host = settings.getSettingValue(ollama_settings, "host")

        self.model_name = ollama_model
        self.host = ollama_host
        self.client = Client( host='http://' + self.host )

    def who_am_i(self):
        super().who_am_i()

    def greet(self):
        super().greet()
    
    def transform(self, code, context):
        puppet_string = ""	

        summary_request = f"""As a software developer take the {context} and change it to a Ansible Playbook and only provide the yaml code and do not display any comments or explanation
        [INPUT]
        {code}
        [SUMMARY]
        """

        response = self.client.generate(self.model_name, summary_request)
        # print(response['response'])
        return response['response']
        
    def handle_general_requst(self,request):
        response = self.client.generate(self.model_name, request)	
        return response['response']