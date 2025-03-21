from .explanator import Explanator
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from fileio.settings import Settings

class WxAI(Explanator):
    def __init__(self):
        settings = Settings()
        wxai_settings = settings.read_sections("settings.config", "watsonx.ai")
        wxai_apikey = settings.getSettingValue(wxai_settings, "api_key")
        wxai_project = settings.getSettingValue(wxai_settings, "project_id")
        wxai_model = settings.getSettingValue(wxai_settings, "model_name")

        self.model_name = wxai_model
        self.api_key = wxai_apikey
        self.project_id = wxai_project

        self.credentials = Credentials(
           url = "https://us-south.ml.cloud.ibm.com", 
           api_key = wxai_apikey
        )

    def who_am_i(self):
        super().who_am_i()

    def greet(self):
        super().greet()
        print(f"API KEY: {self.api_key}")

    def retrieve_tokens(self):
        super.tokens()
   
    def transform(self, code, context):
        client = APIClient(self.credentials)
        reasoning_model = ModelInference(
            model_id=self.model_name,
            api_client=client,
            project_id=self.project_id
        )


        prompt = f"""As a software developer take the {context} and change it to a Ansible Playbook and only provide the yaml code and do not display thought process or any comments or explanation: 
        {code}
        """

        messages = [
            {
                "role": "control",
                "content": "thinking"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}"
                    }
                ]
            }
        ]


        output = reasoning_model.chat(messages=messages)['choices'][0]['message']['content']
        return output
    
       # print(data['results'][0]['generated_text'])
       # return data['results'][0]['generated_text']
    
    def answer_user_query(self,question,references):	
        return
    
    def handle_general_requst(self):
        return super().handle_general_requst()
