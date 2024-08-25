# try:
#     from Configuration import *
#     from MainFunctions.TestGenerator import *
#     from MainFunctions.TestFix import *
#     from MainFunctions.DecisionMaker import *
#     from MainFunctions.BugFix import *

#     print("All imports successful!")
#     testGenerator = TestGenerator(GenUnitTestChain, db, globals())
#     testRegenerator = TestFix(
#         UnitTestFeedbackChain,
#         globals(),
#         True,
#     )
#     # judgeGenerator = DecisionMaker(judgeChain, globals())
#     bugFixGenerator = BugFix(bugFixChain, globals(), True)
# except Exception as e:
#     print(e)
#     exit(-1)


# # #TODO: IMPORTANT find a way to get the code and description from user later
# # for now they are hardcoded


# code = """def add(a, b):\n    return a - b \n"""

# description = "This function adds two numbers"

# isCodeBuggy = True

# # print(isCodeBuggy)
# # isCodeBuggy is accessible here

# codeUnderTest, unitTestCode, feedbackParsed, testsToRepeat, isCodeBuggy = (
#     testGenerator.generate(code, description, isCodeBuggy)
# )
# print("Code Under Test: ", codeUnderTest)
# print("Unit Test Code: ", unitTestCode)
# print("Feedback Parsed: ", feedbackParsed)
# print("Tests to Repeat: ", testsToRepeat)


# # but isCodeBuggy is not accessible here

# if isCodeBuggy:
#     codeUnderTest, unitTestCode, feedbackParsed, testsToRepeat = (
#         bugFixGenerator.generate(
#             description, codeUnderTest, unitTestCode, testsToRepeat, feedbackParsed
#         )
#     )
# else:
#     codeUnderTest, unitTestCode, feedbackParsed, testsToRepeat = (
#         testRegenerator.generate(
#             description, codeUnderTest, unitTestCode, feedbackParsed
#         )
#     )

# print("\n=============================================\nAfter Whichever: ")
# print("Code Under Test: ", codeUnderTest)
# print("Unit Test Code: ", unitTestCode)
# print("Feedback Parsed: ", feedbackParsed)
# print("Tests to Repeat: ", testsToRepeat)



import sys
import re
sys.setrecursionlimit(100)
    


def get_odd_collatz(n):
    if n%2==0:
        odd_collatz = [] 
    else:
        odd_collatz = [n]
    while n > 1:
        if n % 2 == 0:
            n = n/2
        else:
            n = n*3 + 1
            
        if n%2 == 1:
            odd_collatz.append(int(n))

    return sorted(odd_collatz)

import unittest

class TestGetOddCollatz(unittest.TestCase):
    def test_get_odd_collatz_for_one(self):
        result = get_odd_collatz(1)
        self.assertEqual(result, [1])

    def test_get_odd_collatz_for_even_number(self):
        result = get_odd_collatz(4)
        self.assertEqual(result, [1])

    def test_get_odd_collatz_for_odd_number(self):
        result = get_odd_collatz(5)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'])()

