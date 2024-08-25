import re
from time import sleep

# made according to mixtral response
# Skips first code (CUT) and starts searching from after that
def getCodefromTestGeneration(response):
    incompleteResponse = False
    ExtractedResponse = response
    code_match = ""
    # print(response)
    # s = re.finditer(r"```python", response)
    # ExtractedResponse = ""
    # for st in s:
    #     # pick the first code (code under test) in response and ensure its beginning doesn't match with the following patterns
    #     startIndex = st.span(0)[0]
    # ExtractedResponse = response[startIndex:]

    patterns = [
        r"[^\"](?<=```python\n)(.*)\)\n(?=```)",
        r"[^\"](?<=```python\n)(.*)\)\n\n(?=```)",
        r"[^\"](?<=```python\n)(.*)\)(?=```)",
        r"[^\"](?<=```python\n)(.*)",
    ]
    
    for i, pattern in enumerate(patterns):
        code_match = re.search(pattern, ExtractedResponse, re.DOTALL)
        if code_match is not None:
            # if i == len(patterns) - 1:
            #     incompleteResponse = True
            break
    
    # if code_match is None:
    #     return (response[startIndex:], True)
    # print(response)
    # sleep(1)
    if (code_match is None):
        return (response, False)
    
    code = re.sub("from.*(?=class)", "", code_match.group(0), flags=re.DOTALL)
    return code, incompleteResponse


mycode = ("""Here is the unit test for the `even_odd_palindrome` function following the given criteria:\n\n```python\nimport unittest\n\nclass TestEvenOddPalindrome(unittest.TestCase):\n    def test_even_odd_palindrome_when_n_is_three(self):\n        result = even_odd_palindrome(3)\n        self.assertEqual(result, (1, 2))\n\n    def test_even_odd_palindrome_when_n_is_four(self):\n        result = even_odd_palindrome(4)\n        self.assertEqual(result, (2, 1))\n\n    def test_even_odd_palindrome_when_n_is_five(self):\n        result = even_odd_palindrome(5)\n        self.assertEqual(result, (2, 2))\n\n    def test_even_odd_palindrome_when_n_is_six(self):\n        result = even_odd_palindrome(6)\n""")
code, tc = getCodefromTestGeneration(mycode)
print(tc)
# skips any substring that contains a statement from the prompt template
# handles only if the llm changes either the code or the test cases
# TODO: handle if the llm changes both the code and the test cases
def getCodeFromTestFixing(response, 
        promptStatementToCheck = "Your goal is to revise the code or tests based on the feedback. Ensure to:"):
    incompleteResponse = False

    s = re.finditer(r"```python", response)
    ExtractedResponse = ""
    for st in s:
        # pick a statement from the prompt template and ensure it's no in the chosen repsonse
        startIndex = st.span(0)[0]
        ExtractedResponse = response[startIndex:]
        if promptStatementToCheck in ExtractedResponse:
            continue
        else:
            break
    # question mark is added to make the match non-greedy
    # the last ) is added to make sure the code ends with a closing bracket and that we are getting the test case code
    patterns = [
        r"[^\"](?<=```python\n)(.*)?\)\n(?=```)",
        r"[^\"](?<=```python\n)(.*)?\)\n\n(?=```)",
        r"[^\"](?<=```python\n)(.*)?\)(?=```)",
        r"[^\"](?<=```python\n)(.*)?",
    ]
    
    for i, pattern in enumerate(patterns):
        code_match = re.search(pattern, ExtractedResponse, re.DOTALL)
        if code_match is not None:
            if i == len(patterns) - 1:
                incompleteResponse = True
            break

    if code_match is None:
        return (response[startIndex:], True)
    code = re.sub("from.*(?=class)", "", code_match.group(0), flags=re.DOTALL)
    return code, incompleteResponse


def getCodeFromBugFixing(
    response,
    promptStatementToCheck="</s> [/INST]",
):
    incompleteResponse = False

    s = re.finditer(r"```python", response)
    ExtractedResponse = ""
    for st in s:
        # pick a statement from the prompt template and ensure it's no in the chosen repsonse
        startIndex = st.span(0)[0]
        ExtractedResponse = response[startIndex:]
        if promptStatementToCheck in ExtractedResponse:
            continue
        else:
            break
    # question mark is added to make the match non-greedy
    patterns = [
        r"```python\n(.*?)```",
        r"```python\n(.*?)```\n",
        r"```python\n(.*?)",
    ]
    for i, pattern in enumerate(patterns):
        code_match = re.search(pattern, ExtractedResponse, re.DOTALL)
        if code_match is not None:
            if i == len(patterns) - 1:
                incompleteResponse = True
            break

    if code_match is None:
        return (response[startIndex:], True)
    code = code_match.group(0)
    code = code.replace("```python\n", "").replace("```", "")
    return code, incompleteResponse


def getCodeFromResponse(response, testFixing=0):
    # res = re.findall(r"if __name__ == \'__main__\':", response, re.DOTALL)
    # if (len(res) == 1): # that means there is only one main call which is in the prompt description not generated by the model
    #     addedCall = "\nif __name__ == '__main__':\n\tunittest.main()```"
    #     response += addedCall
    
    if testFixing == 0:
        return getCodefromTestGeneration(response)
    elif testFixing == 1:
        return getCodefromTestGeneration(response)
    else:
        # for bug fixing
        return getCodeFromBugFixing(response, "</s> [/INST]")


def getEachTestCase(UnitTestsCode, functionNames):
    """Extract test cases code according to given function names"""
    # First split the test cases
    if len(functionNames) == 0:
        return UnitTestsCode
    classHeader = re.search(r"(class.*:)", UnitTestsCode)
    method_pattern = r"""
    (def\s+        # Match 'def' keyword followed by whitespace
    ({0})         # Capture method signature using a named capturing group (1) 
                   #  where {0} is replaced with the joined method names
    \(.*?\)     
    \s*:)\n        # Match whitespace, colon, and whitespace
    (.*?)          # Capture method body (non-greedy) - group (3)
    (?=\n\s*def|\n\Z) # Positive lookahead to ensure not followed by another 'def' or end of string
    """.format(
        "|".join(functionNames)
    )  # Replace {0} with joined method names
    tests = []
    matches = re.finditer(
        method_pattern, UnitTestsCode, flags=re.DOTALL | re.MULTILINE | re.VERBOSE
    )
    for functionmatch in matches:
        method_defintion = functionmatch.group(1)
        method_body = functionmatch.group(3)
        method_body_lines = method_body.split("\n")
        method_body = "\n".join(["\t" + line for line in method_body_lines])
        tests.append("\t" + method_defintion + "\n" + method_body)
    tests = "\n".join(tests)
    editPattern = """if __name__ == '__main__':"""
    index = tests.find(editPattern)
    if index != -1:
        mainCall = tests[index:]
        mainCall_lines = mainCall.split("\n")
        mainCall = "\n" + mainCall_lines[0] + "\n\t" + mainCall_lines[1].strip()
        tests = tests[:index] + mainCall  # Slice up to the index of the substring
    code = "\nimport unittest\n\n" + classHeader.group(0) + "\n" + tests
    return code


def regeneratePrompt(chat_model_arb, code, description, testcase):
    reGenerationPrompt = f"""
    you generated unittest for the following method under test having the following description:
    *Method under test*:
    {code}

    *Description*:
    {description}


    but this test failed
    *Test*:
    {testcase}


    Preserve the indentation correctness in the response
    fix only the unit test and re-run the code. The code should pass the test after the fix and enclosed by ```python and ``` to be able to run the code
    """

    res = (chat_model_arb.invoke(reGenerationPrompt)).content
    return res


# assumes following the first template:
# Bug in the python code under test: **IS_METHOD_UNDER_TEST_BUGGY**
# Explanation: **EXPLANATION**
# def getJudgmentFromGeneration(response):
#     incompleteResponse = False
#     s = re.finditer(r"</s> \[/INST\]", response)
#     # gets last element in iterator
#     *_, lastMatch = s
#     startIndex = lastMatch.span(0)[1]
#     ExtractedResponse = response[startIndex:]
#     judgementMatch = re.search(
#         r"Bug in the python code under test: (True|False)", ExtractedResponse
#     )
#     explanationMatch = re.search(r"Explanation:", ExtractedResponse)

#     if judgementMatch is None:
#         return (response[startIndex:], "", True)
#     judgement = judgementMatch.group(1)
#     expIndex = explanationMatch.end()
#     explanation = ExtractedResponse[expIndex:]
#     return judgement, explanation, incompleteResponse


def getJudgmentFromGeneration(response):
    incompleteResponse = False
    s = re.finditer(r"</s> \[/INST\]", response)
    # gets last element in iterator
    *_, lastMatch = s
    startIndex = lastMatch.span(0)[1]
    ExtractedResponse = response[startIndex:]
    judgementMatchCodeBuggy = re.search(
        r"Bug in the Code: (True|False)", ExtractedResponse
    )
    if judgementMatchCodeBuggy is None:
        # assume he forgot to write Bug in the Code: False
        judgementCodeBuggy = "False"
    else:
        judgementCodeBuggy = judgementMatchCodeBuggy.group(1)

    judgementMatchTestBuggy = re.search(
        r"Bug in the test case: (True|False)", ExtractedResponse
    )
    if judgementMatchTestBuggy is None:
        # assume he forgot to write Bug in the test case: False
        judgementTestBuggy = "False"
    else:
        judgementTestBuggy = judgementMatchTestBuggy.group(1)
    # if both are None, then the response is incomplete
    if judgementMatchCodeBuggy is None and judgementMatchTestBuggy is None:
        incompleteResponse = True
        return (response[startIndex:], "", "", True)

    explanationMatch = re.search(r"Explanation:", ExtractedResponse)
    expIndex = explanationMatch.end()
    explanation = ExtractedResponse[expIndex:]
    return judgementCodeBuggy, judgementTestBuggy, explanation, incompleteResponse
