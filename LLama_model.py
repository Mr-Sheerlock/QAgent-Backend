from typing import List, Dict
from prompts_text import *
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from llama_index.core import PromptTemplate


 


# URL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
# remotely_run = HuggingFaceInferenceAPI(
#     model_name="HuggingFaceH4/zephyr-7b-alpha", token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
# )

# completion_response = remotely_run.complete("To infinity, and")
# print(completion_response)

class LlamaModel:
    __model = None
    __type = None # types are: 1 for test generation, 2 for test fix, 3 for bug fix
    __template = None
    # def __init__(self, model: HuggingFaceLLM):
    #     self.model = model


    def invoke(self, prompt: Dict):
        prompt_final = ""
        if (self.__type == 1):
            prompt_final = self.__template.format(description=prompt["description"], code=prompt["code"], test_cases_of_few_shot=prompt["test_cases_of_few_shot"])
            
        elif (self.__type == 2):
            prompt_final = self.__template.format(description=prompt["description"], code=prompt["code"], UnitTests=prompt["UnitTests"], Feedback=prompt["Feedback"])
        
        
        
        return self.__model.complete(prompt_final)

    def InitializeModel(self, htoken, model_name="mistralai/Mixtral-8x7B-Instruct-v0.1", max_new_tokens=20000, type=1):
        llm = HuggingFaceInferenceAPI(model_name = model_name, token = htoken, max_tokens = max_new_tokens, temperature = 0.1)
        self.__type = type
        self.__model = llm
        if (type == 1):
            self.__template = PromptTemplate(addMixtralTokens(Gen_UnitTest_with_FewShots_template))
        elif (type == 2):
            self.__template = PromptTemplate(addMixtralTokens(RegenerateTestTemplate))
            
        return llm

    def get_model(self):
        return self.__model

