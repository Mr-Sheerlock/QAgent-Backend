from Imports import *
from utils.CustomThread import *


class BugFix:

    def __init__(
        self,
        BugFixChain,
        firstFeedback,
        myglobals,
    ):
        self.reset()
        self.BugFixChain = BugFixChain
        self.myglobals = myglobals
        self.firstFeedback = firstFeedback

    def reset(self):
        self.totalTestCasesNum = 0
        self.totalSuccessTestCasesNum = 0
        self.failed_test_cases = 0
        self.error_test_cases = 0
        self.failedExamplesNum = 0
        self.successfulExamplesNum = 0
        self.apiErrors = 0
        self.testsToRepeat = 0  # Number of tests to repeat = Summation of all tests under failed examples whether they are failed or succeeded
        self.OKCases = 0
        self.descriptions = []
        self.codes = []
        self.resCodes = []
        self.feedbacks = []
        self.codeRanList = []
        self.TotalCases = 0
        self.TotalFailedCases = 0
        self.incompleteResponses = 0
        self.OutputFolder = "BugFixOutput/"
        self.JSONFile = self.OutputFolder + "RunningLogs.json"
        self.CasesJSONFile = self.OutputFolder + "Cases.json"
        OldGeneratedTestsFolder = "OutputTest/"
        JudgeFolder = "JudgeOutput/"
        self.OldCasesFile = OldGeneratedTestsFolder + "Cases.json"
        self.OldJsonFile = JudgeFolder + "JudgmentLogs.json"
        self.CasesLogs = pd.read_json(self.OldJsonFile)
        self.OldCases = pd.read_json(self.OldCasesFile)
        self.logsDf = pd.DataFrame()
        self.casesDf = pd.DataFrame()
        self.firstFeedback = True

    def generate(self):
        """
        This function is responsible for Fixing Bugs in Code and running the code with generated tests
        The function is responsible for:
        1. Extracting the code and description from the example
        2. Fixing Bugs in Code
        3. Running the test cases
        4. Storing the results in a JSON file
        Args: None
        Return: None
        """
        print(self.firstFeedback)
        self.checkPaths()
        self.reset()
        c = open(self.OutputFolder + "Cases.txt", "w+")
        for i in range(len(self.CasesLogs)):
            # if (i == 28):
            #     x = 9000
            print("Running Example ", i, "\n=====================\n")

            (
                currDescription,
                currCode,
                Judgement,
                Explanation,
                ErrorTestCases,
                ErrorMessage,
            ) = self.extractInfo(i)
            # no feedback means testcase passed so don't run it again
            # truncated from step before
            # if (
            #     "OK" in currFeedback
            #     or pd.isna(currFeedback)
            #     or currFeedback == ""
            #     or currFeedback is None
            # ):
            #     print("Example", i, " has already passed")
            #     c.write(
            #         "Example "
            #         + str(i)
            #         + " has already passed\n=====================================\n"
            #     )
            #     continue
            if Judgement == "True":
                print("Example", i, " has been judged to contain erroneous test cases")
                c.write(
                    "Example "
                    + str(i)
                    + " has been judged to contain erroneous test cases\n=====================================\n"
                )
                continue

            try:
                GeneratedBugFix = self.BugFixChain.invoke(
                    {
                        "description": currDescription,
                        "code": currCode,
                        "test_case_error": None,
                        "error_message": ErrorMessage,
                        "explanation": Explanation,
                    }
                )
            except Exception as e:
                print("ERROR in invoking Feedback Chain")
                self.apiErrors += 1
                print(e)
                c.write(
                    "Example "
                    + str(i)
                    + " Didn't Run Due to Errorr\n=====================================\n"
                )
                continue
            newCode, isIncompleteResponse = getCodeFromResponse(
                GeneratedBugFix["text"], 3
            )
            if isIncompleteResponse:
                self.incompleteResponses += 1
                print(
                    "Test Case "
                    + str(i)
                    + " Didn't Run Due to Incomplete Response\n=====================================\n"
                )
                c.write(
                    "Example "
                    + str(i)
                    + " Didn't Run Due to Incomplete Response\n=====================================\n"
                )
            unittestCode = preprocessUnitTest(ErrorTestCases)
            codeTobeRun = getRunningCode(newCode, unittestCode)
            feedback = runCode(codeTobeRun, self.myglobals)
            NonSucceedingCasesNames = getNonSucceedingTestcases(feedback)
            NonSucceedingCasesNamesList = (
                NonSucceedingCasesNames["failed"] + NonSucceedingCasesNames["error"]
            )
            testsToRepeat = getEachTestCase(unittestCode, NonSucceedingCasesNamesList)
            feedbackparsed = getFeedbackFromRun(feedback)
            self.writeResults(
                feedback,
                feedbackparsed,
                unittestCode,
                c,
                NonSucceedingCasesNamesList,
                i,
            )
            self.descriptions.append(currDescription)
            self.codes.append(currCode)
            self.resCodes.append(unittestCode)
            self.feedbacks.append(feedbackparsed)  # feedbackparsed
            newRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Description": currDescription,
                    "Code": currCode,
                    "GeneratedCode": newCode,
                    "CodeRan": codeTobeRun,
                    "Feedback": feedbackparsed,
                    "FullFeedback": feedback,
                    "TestsToRepeat": testsToRepeat,
                },
                index=[0],
            )
            # df = df.append(newRow, ignore_index=True)
            self.logsDf = pd.concat([self.logsDf, newRow])
            # Save the updated DataFrame back to the excel file using 'openpyxl' engine for writing
            jsondata = self.logsDf.to_dict(orient="records")
            with open(self.JSONFile, "w") as f:
                json.dump(jsondata, f, indent=4)

        self.printResults()
        c.close()
        return

    def extractInfo(self, i):
        """
        Extract the description and code from the example in addition to prepending the function header
        Args: i (int): The index of the example in the JSON file
        Return: description (str): The description of the example
                code (str): The code of the example
                generatedCode (str): The generated code of the example
                feedback (str): The feedback of the example
        """
        currDescription = self.CasesLogs.iloc[i]["Description"]
        currCode = self.CasesLogs.iloc[i]["Code"]
        Judgement = self.CasesLogs.iloc[i]["Judgement"]
        Explanation = self.CasesLogs.iloc[i]["Explanation"]
        TestCaseError = self.CasesLogs.iloc[i]["TestCaseError"]
        ErrorMessage = self.CasesLogs.iloc[i]["ErrorMessage"]
        # test_case_error
        # error_message
        # explanation

        return (
            currDescription,
            currCode,
            Judgement,
            Explanation,
            TestCaseError,
            ErrorMessage,
        )

    def checkPaths(self):
        """
        Check if these directories and files exist, if not create them
        Args: None
        Return: None
        """
        if not os.path.exists(self.OutputFolder):
            try:
                os.makedirs(self.OutputFolder)
                print(f"Directory {self.OutputFolder} created successfully!")
            except Exception as e:
                print(f"Error creating directory {self.OutputFolder}: {e}")
                exit()

        if not os.path.exists(self.CasesJSONFile):
            try:
                # Create a new empty JSON file with an empty list structure
                with open(self.CasesJSONFile, "w") as f:
                    json.dump([], f)
                print(f"File {self.CasesJSONFile} created successfully!")
            except Exception as e:
                print(f"Error creating file {self.CasesJSONFile}: {e}")
                exit()

        if not os.path.exists(self.JSONFile):
            try:
                # Create a new empty JSON file with an empty list structure
                with open(self.JSONFile, "w") as f:
                    json.dump([], f)
                    print(f"File {self.JSONFile} created successfully!")
            except Exception as e:
                print(f"Error creating file {self.JSONFile}: {e}")
                exit()

    def writeResults(
        self, feedback, feedbackparsed, unittestCode, c, NonSucceedingCasesNamesList, i
    ):
        """
        Responsible for writing results to cases.txt and cases.json

        Args: feedbackparsed (str): The parsed feedback from the test case


        """
        numOfAssertions = getNumAssertions(unittestCode)
        if feedbackparsed == "" or feedbackparsed is None:
            # in case of OK
            self.successfulExamplesNum += 1
            self.OKCases += 1
            print(
                f"Test example {i} succeeded\n======================================\n"
            )
            print("Number of Ran Tests : ", numOfAssertions)
            print("Number of Succeeded Test : ", numOfAssertions)
            print("Number of Succeeded Test : ", 0)
            c.write("Test example " + str(i) + " succeeded\n")
            c.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
            c.write("Number of Succeeded Test : " + str(numOfAssertions) + "\n")

            oldTotalTests = 0
            oldTestsFailed = 0
            oldTestsError = 0
            if self.firstFeedback:
                oldTotalTests = self.OldCases.iloc[i]["Total Tests"]
                oldTestsFailed = self.OldCases.iloc[i]["Tests failed"]
                oldTestsError = self.OldCases.iloc[i]["Error Tests"]
            else:
                oldTotalTests = self.OldCases.iloc[i]["Feedback Total Tests"]
                oldTestsFailed = self.OldCases.iloc[i]["Feedback Tests failed"]
                oldTestsError = self.OldCases.iloc[i]["Feedback Error Tests"]

            newCaseRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Feedback Total Tests": numOfAssertions,
                    "Feedback Tests failed": 0,
                    "Feedback Error Tests": 0,
                    "Old Total Tests": oldTotalTests,
                    "Old Tests Failed": oldTestsFailed,
                    "Old Tests Error": oldTestsError,
                },
                index=[0],
            )
            self.casesDf = pd.concat([self.casesDf, newCaseRow])
            casejsondata = self.casesDf.to_dict(orient="records")
            with open(self.CasesJSONFile, "w") as f:
                json.dump(casejsondata, f, indent=4)

            self.totalTestCasesNum += numOfAssertions

        else:
            if (
                "syntaxerror" in feedbackparsed.lower()
                or "indentationerror" in feedbackparsed.lower()
                or "timed out" in feedbackparsed.lower()
            ):
                print(
                    f"Test example {i} failed due to syntax or indentation or timeout\n======================================\n"
                )
                print("Number of Ran Tests : ", 0)
                print("Number of failed Tests : ", 0)
                print("Number of error Tests : ", 1)
                print("Number of Succeeded Test : ", 0)
                c.write(
                    "Test example "
                    + str(i)
                    + " failed due to syntax or indentation or timeout\n"
                )
                c.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
                c.write("Number of failed Tests : " + str(0) + "\n")
                c.write("Number of Error Test : " + str(1) + "\n")
                c.write("Number of Succeeded Test : " + str(0) + "\n")
                self.failedExamplesNum += 1
                return
            self.failedExamplesNum += 1
            failedCasesNum, errorCasesNum = getNumNonSucceedingTestcases(feedback)
            numberOfSucceeded = numOfAssertions - failedCasesNum - errorCasesNum
            print(f"Test example {i} failed\n======================================\n")
            print("Number of Ran Tests : ", numOfAssertions)
            print("Number of failed Tests : ", failedCasesNum)
            print("Number of error Tests : ", errorCasesNum)
            print(
                "Number of Succeeded Test : ",
                numberOfSucceeded,
            )
            c.write("Test example " + str(i) + " failed\n")
            c.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
            c.write("Number of failed Tests : " + str(failedCasesNum) + "\n")
            c.write("Number of Error Test : " + str(errorCasesNum) + "\n")
            c.write("Number of Succeeded Test : " + str(numberOfSucceeded) + "\n")

            if self.firstFeedback:
                oldTotalTests = self.OldCases.iloc[i]["Total Tests"]
                oldTestsFailed = self.OldCases.iloc[i]["Tests failed"]
                oldTestsError = self.OldCases.iloc[i]["Error Tests"]
            else:
                oldTotalTests = self.OldCases.iloc[i]["Feedback Total Tests"]
                oldTestsFailed = self.OldCases.iloc[i]["Feedback Tests failed"]
                oldTestsError = self.OldCases.iloc[i]["Feedback Error Tests"]
            # print("Old Error Tests", oldTestsError)

            newCaseRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Feedback Total Tests": numOfAssertions,
                    "Feedback Tests failed": failedCasesNum,
                    "Feedback Error Tests": errorCasesNum,
                    "Old Total Tests": oldTotalTests,
                    "Old Tests Failed": oldTestsFailed,
                    "Old Tests Error": oldTestsError,
                },
                index=[0],
            )
            self.casesDf = pd.concat([self.casesDf, newCaseRow])
            casejsondata = self.casesDf.to_dict(orient="records")
            with open(self.CasesJSONFile, "w") as f:
                json.dump(casejsondata, f, indent=4)
            self.testsToRepeat += len(NonSucceedingCasesNamesList)
            self.totalTestCasesNum += numOfAssertions
            self.failed_test_cases += failedCasesNum
            self.error_test_cases += errorCasesNum

    def printResults(self):
        """
        Prints the remaining results and create Res.txt which includes a summary of the overall run

        """
        print("\n End of Test Cases \n")
        print("Total succeeded examples : ", self.successfulExamplesNum)
        print("Total failed examples : ", self.failedExamplesNum)
        print("Total  testcases : ", self.totalTestCasesNum)
        print(
            "Total succeeded testcases : ",
            self.totalTestCasesNum
            - self.failed_test_cases
            - self.incompleteResponses
            - self.error_test_cases,
        )
        print("Total failed testcases : ", self.failed_test_cases)
        print("Total error testcases : ", self.error_test_cases)
        print("Tests to repeat : ", self.testsToRepeat)
        print("Incomplete Responses are : ", self.incompleteResponses)
        print("API Errors are : ", self.apiErrors)
        with open(self.OutputFolder + "Res.txt", "w") as f:
            f.write(
                "Total succeeded examples : " + str(self.successfulExamplesNum) + "\n"
            )
            f.write("Total failed examples : " + str(self.failedExamplesNum) + "\n")
            f.write("Total  testcases : " + str(self.totalTestCasesNum) + "\n")
            f.write(
                "Total succeeded testcases : "
                + str(
                    self.totalTestCasesNum
                    - self.failed_test_cases
                    - self.incompleteResponses
                    - self.error_test_cases
                    - self.apiErrors
                )
                + "\n"
            )
            f.write("Total failed testcases : " + str(self.failed_test_cases) + "\n")
            f.write("Total error testcases : " + str(self.error_test_cases) + "\n")
            f.write(
                "Incomplete Responses are : " + str(self.incompleteResponses) + "\n"
            )
            f.write("API Errors are : " + str(self.apiErrors) + "\n")
            f.write("Tests to repeat : " + str(self.testsToRepeat) + "\n")

        print("Incomplete Responses are ", self.incompleteResponses)
