##### This file contains the utility functions for preprocessing string for either fewshot or running the code. ######
import re


def addMixtralTokens(template):
    """Adds Mixtral Special Tokens to the prompt in case of vanilla llm by API to try to prevent incomplete responses problem."""
    return "<s> [INST] " + template + "</s> [/INST]"


def removeMetaData(unittests):
    """
    Removes the METADATA block from the unit tests that is not needed for the code to run and present in HUMANEVAL dataset
    Args: unittests: list of unit tests
    Returns: list of unit tests with METADATA block removed
    """
    output = []
    for unitest in unittests:
        # pattern = re.compile(r"\bMETADATA\b\s*=\s*{.*}", re.DOTALL)

        # Use the sub() method to remove the matched block
        modified_unit_test = re.sub(
            "METADATA\s*=\s*\{([^}]*)\}", "", unitest, re.DOTALL
        ).lstrip("\n")
        output.append(modified_unit_test)
    return output


# preprocesses the prompt string to be used in the few shot learning
def preprocessStringFewShot(codes, example_unit_tests):
    """Preprocesses the prompt string to be used in the few shot learning puts it in the format:
    {"examples": [{"input 1": "code", "output 1": "test_case"}, ...]"""
    string_few_shot = ""
    string_few_shot += '{\n"examples": ['
    open_curly = "{"
    close_curly = "}"
    index = 0
    code_prepend = " \"Code \n'''python\n"
    test_case_prepend = " \"Example unit tests \n'''python\n"
    code_append = test_case_append = "'''\n\""

    for i in zip(codes, example_unit_tests):
        index += 1
        string_few_shot += (
            open_curly
            + f'"input {index}":'
            + code_prepend.format(index=index)
            + i[0]
            + code_append
            + f', "output {index}":'
            + test_case_prepend.format(index=index)
            + i[1]
            + test_case_append
            + "},\n"
        )
    # remove the last comma
    string_few_shot = string_few_shot[:-2]
    string_few_shot += "]\n}"
    return string_few_shot


# replaces the unittest call with another one to fix exec problem with running on colab
def replaceUnitTestCall(code):
    """
    This makes the unittest call compatible when running on Jupyter Notebooks or Google Colab.
    """
    pattern = r"unittest.main()"

    # Use re.sub() to replace the pattern with the replacement string
    modified_code = re.sub(
        pattern, "unittest.main(argv=['first-arg-is-ignored'])", code
    )

    return modified_code


def addUnitTestImport(code):
    pattern = r"import unittest"

    ## search for the pattern in code and add it if not present
    if re.search(pattern, code):
        return code
    else:
        modified_code = "import unittest\n" + code
        return modified_code


# adds the unittest call to the code if not present
def addUnitTestCall(code):
    pattern = r"if __name__ == '__main__':\n    unittest.main\(\)"
    match = re.search(pattern, code)
    if match:
        return code
    else:
        modified_code = code + "\nif __name__ == '__main__':\n    unittest.main()"
        return modified_code


def preprocessUnitTest(code):
    code = addUnitTestCall(code)
    code = replaceUnitTestCall(code)
    code = addUnitTestImport(code)
    code = re.sub(
        r"\\_", "_", code
    )  # added to remove the extra \\_ in the generated code

    return code





def getRunningCode(codeUnderTest, unitTestCode):
    """Takes in the code under test and the unittest code and returns the code to run"""
    
    # intro code indentation is important for the code to run
    introCode = """
import sys
import re
sys.setrecursionlimit(100)
    """
    runningCode = introCode + "\n" + codeUnderTest + "\n" + unitTestCode
    return runningCode
