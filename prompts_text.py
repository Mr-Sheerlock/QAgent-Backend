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


RegenerateTestTemplate = """You are a Python expert, and your task is to debug and improve the following Python unitTest code based on the given description, code snippet, and unit tests feedback:

*Description:*
{description}

*Given Code under Test:*
{code}

You previously generated the following code as unit tests:
*Unit Tests:*
{UnitTests}

After running the code with these tests, you received the following feedback based on the test output:
*Feedback:*
{Feedback}

Your goal is to revise the tests based on the feedback. Ensure to:
ADDRESS all highlighted bugs in the feedback.
MODIFY only the unit tests
DO NOT include new imports for the tests.
PRESERVE all existing functionality not related to the bugs.

RETURN your revised unit tests as only one formatted markdown code snippet without further explanation, surrounded by triple backticks and the word 'python'."""


def addMixtralTokens(template):
    """Adds Mixtral Special Tokens to the prompt in case of vanilla llm by API to try to prevent incomplete responses problem."""
    return "<s> [INST] " + template + "</s> [/INST]"
