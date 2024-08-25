from Imports import *
from utils.CustomThread import *


class TestFix:

    def __init__(
        self,
        UnitTestFeedbackChain,
        myglobals,
        firstFeedback=True,
    ):
        self.UnitTestFeedbackChain = UnitTestFeedbackChain
        self.myglobals = myglobals
        self.firstFeedback = firstFeedback

    def generate(self, Description, codeUnderTest, oldGeneratedTestCode, oldFeedback):
        """
        This function is responsible for generating the test cases and running them
        The function is responsible for:
        1. Extracting the code and description from the example
        2. Generating the test cases
        3. Running the test cases
        4. Storing the results in a JSON file
        Args: None
        Return: None
        """
        # Description, codeUnderTest, oldGeneratedTestCode, oldFeedback = (
        #     self.extractInfo(i)
        # )
        # no feedback means testcase passed so don't run it again
        if ( "OK" in oldFeedback or pd.isna(oldFeedback) or oldFeedback == "" or oldFeedback is None ):
            print("Example has already passed")  ## you have to stop here!!!
        try:
            GenerationPostFeedback = self.UnitTestFeedbackChain.invoke(
                {
                    "description": Description,
                    "code": codeUnderTest,
                    "UnitTests": oldGeneratedTestCode,
                    "Feedback": oldFeedback,
                }
            )
        except Exception as e:
            print("ERROR in invoking Feedback Chain")
            print(e)
        newUnitTestCode, isIncompleteResponse = getCodeFromResponse(
            GenerationPostFeedback["text"], 1
        )
        if isIncompleteResponse:
            print(
                "Test Case Didn't Run Due to Incomplete Response\n=====================================\n"
            )
        unittestCode = preprocessUnitTest(newUnitTestCode)
        codeTobeRun = getRunningCode(codeUnderTest, unittestCode)
        feedback = runCode(codeTobeRun, self.myglobals)
        NonSucceedingCasesNames = getNonSucceedingTestcases(feedback)
        NonSucceedingCasesNamesList = (
            NonSucceedingCasesNames["failed"] + NonSucceedingCasesNames["error"]
        )
        testsToRepeat = getEachTestCase(unittestCode, NonSucceedingCasesNamesList)
        feedbackparsed = getFeedbackFromRun(feedback)
        return codeUnderTest, unittestCode, feedbackparsed, testsToRepeat
