from huggingface_hub import InferenceClient
from typing import Dict
from prompts_text import *
from llama_index.core import PromptTemplate




class HFCustomInferenceAPI:
    __model = None
    __type = None # types are: 1 for test generation, 2 for test fix, 3 for bug fix
    __template = None
    __max_tokens = None
    # def __init__(self, model: HuggingFaceLLM):
    #     self.model = model

    def inferFun(self, prompt):
        response = ""
        for message in self.__model.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.__max_tokens,
            stream=True,
            temperature=0.1
        ):
            response += message.choices[0].delta.content
        return response


    def invoke(self, prompt: Dict):
        prompt_final = ""
        if (self.__type == 1):
            prompt_final = self.__template.format(description=prompt["description"], code=prompt["code"], test_cases_of_few_shot=prompt["test_cases_of_few_shot"])
            
        elif (self.__type == 2):
            prompt_final = self.__template.format(description=prompt["description"], code=prompt["code"], UnitTests=prompt["UnitTests"], Feedback=prompt["Feedback"])
        
        # print(prompt_final)
        return self.inferFun(prompt_final)

    def InitializeModel(self, htoken, model_name="mistralai/Mixtral-8x7B-Instruct-v0.1", max_new_tokens=20000, type=1):
        llm = InferenceClient(
            model=model_name,
            token=htoken,
        )
        
        self.__max_tokens = max_new_tokens
        self.__type = type
        self.__model = llm
        if (type == 1):
            self.__template = PromptTemplate((Gen_UnitTest_with_FewShots_template))
        elif (type == 2):
            self.__template = PromptTemplate((RegenerateTestTemplate))

        return llm


    # def get_model(self):
    #     return self.__model

