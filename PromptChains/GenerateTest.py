from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceHub
from langchain_community.chat_models.huggingface import ChatHuggingFace
import openai
from utils.PreprocessUtils import addMixtralTokens

GenerateTestTemplate = """You are a python expert and your task is: Given the following description and python code:
Description:
{description}
Code:
'''python
{code}'''
Generate a class that contains at least 7 unit tests (where each test has only one assertion) written in python that acheive high coverage to find bugs, runtime errors or logical errors in the code according to the description and include any required imports.
Make sure to include the unit test call unittest.main() to run the tests. Do not include any import for the code under test.
The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "```python" and "```" respectively:"""

Gen_UnitTest_with_FewShots_templatelol = """You are a python expert and your task is: Given the following description and python code:
Description:
{description}
Code:
'''python
{code}'''
Generate a class that contains at least 7 unit tests (where each test has only one assertion) written in python that acheive high coverage to find bugs, runtime errors or logical errors in the code to conform with the description and include any required imports.
Do not include import for the code under test in the unit tests.
You are given examples of unit tests for a similar code, which you can use to write the unit tests for the given code.:
{test_cases_of_few_shot}
Make sure to include the unit test call unittest.main() to run the tests.
The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "```python" and "```" respectively:"""

Gen_UnitTest_with_FewShots_template = """You are python unit tester, Write at least 7 unit tests for a method under test. You follow my rules and orders and if you do not know the answer, don't make things UP!
I am going to give you a method under test as well as its description and you are going to follow the criteria that I give to you in the generation.
Criteria:
Write 7 test cases that capture the intent of the user and create asserts that match descrition.
Each test generated contains only one assertion.
Complete the unittest code till "unittest.main()" is called. Think before you end the response. I do not want any incomplete code.
Do not include import for the method under test in the unit tests.
Run the tests and see if they match the description. If not, change the assertions to match the description.

Method under test:
{code}

Description:
{description}

I am going to add similar functions and their corresponding test cases that you may need to use in your tests. You can use them in your tests.
{test_cases_of_few_shot}

I am going to to give you a template for your output where:
Replace **TESTMETHODUNDERTEST** with the right name for the class.
2- Replace **TEST_CASES_WITH_UNDERSTANDABLE_NAMES** with the test cases that you generated.
My template is:
```python
import unittest

class **TESTMETHODUNDERTEST**(unittest.TestCase):
    **TEST_CASES_WITH_UNDERSTANDABLE_NAMES**

if __name__ == '__main__':
    unittest.main()
```
Evaluate your generated test cases and change the assertions if needed to comply with the description. Do not make things up!
"""


def InitializeTestChain(llm, fewshots=False):
    global GenerateTestTemplate
    global Gen_UnitTest_with_FewShots_template
    # adding [INST] to mixtral manually
    if isinstance(llm, HuggingFaceHub) and "Mixtral" in llm.repo_id:
        GenerateTestTemplate = addMixtralTokens(GenerateTestTemplate)
        Gen_UnitTest_with_FewShots_template = addMixtralTokens(
            Gen_UnitTest_with_FewShots_template
        )
    if isinstance(llm, ChatHuggingFace):
        GenerateTestTemplate = addMixtralTokens(GenerateTestTemplate)
        Gen_UnitTest_with_FewShots_template = addMixtralTokens(
            Gen_UnitTest_with_FewShots_template
        )
    
    if not fewshots:
        Generate_Unit_Tests_Template = PromptTemplate(
            template=GenerateTestTemplate,
            input_variables=["description", "code"],
            verbose=False,
        )
    else:
        Generate_Unit_Tests_Template = PromptTemplate(
            template=Gen_UnitTest_with_FewShots_template,
            input_variables=["description", "code", "test_cases_of_few_shot"],
            verbose=False,
        )

    GenUnitTestChain = LLMChain(
        llm=llm, verbose=False, prompt=Generate_Unit_Tests_Template
    )
    return GenUnitTestChain


# def CallTestChain(llm, description, code, fewshots=False, test_cases_of_few_shot=None):
#     GenUnitTestChain = InitializeTestChain(llm, fewshots)
#     if not fewshots:
#         response = GenUnitTestChain.run(description=description, code=code)
#     else:
#         response = GenUnitTestChain.run(
#             description=description,
#             code=code,
#             test_cases_of_few_shot=test_cases_of_few_shot,
#         )
#     return response


def createPromptStringGenerateTest(
    description, code, fewshots=False, test_cases_of_few_shot=None
):
    if not fewshots:
        prompt = GenerateTestTemplate.format(description=description, code=code)
    else:
        prompt = Gen_UnitTest_with_FewShots_template.format(
            description=description,
            code=code,
            test_cases_of_few_shot=test_cases_of_few_shot,
        )
    return prompt


def queryGptGenerateTest(
    model, description, code, fewshots=False, test_cases_of_few_shot=None
):
    prompt = createPromptStringGenerateTest(
        description, code, fewshots, test_cases_of_few_shot
    )
    
    response = openai.ChatCompletion.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )

    return response
