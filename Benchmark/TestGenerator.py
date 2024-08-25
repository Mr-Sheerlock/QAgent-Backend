from Imports import *
from utils.CustomThread import *


class TestGenerator:

    def __init__(self, GenUnitTestChain, db, data_JsonObj, myglobals, isHumanEval=True):
        self.reset()
        self.GenUnitTestChain = GenUnitTestChain
        self.db = db
        self.data_JsonObj = (
            data_JsonObj  # data json object , previously humanEval_JsonObj
        )
        self.myglobals = myglobals
        self.isHumanEval = isHumanEval
        self.interfaceModerator = "HF"  # the interface with huggingface

    def reset(self):
        self.totalTestCasesNum = 0
        self.totalSuccessTestCasesNum = 0
        self.failed_test_cases = 0
        self.error_test_cases = 0
        self.failedExamplesNum = 0
        self.successfulExamplesNum = 0
        self.apiErrors = 0
        self.testsToRepeatNum = 0  # Number of tests to repeat = Summation of all tests under failed examples whether they are failed or succeeded
        self.OKCases = 0
        self.descriptions = []
        self.codes = []
        self.resCodes = []
        self.feedbacks = []
        self.codeRanList = []
        self.TotalCases = 0
        self.TotalFailedCases = 0
        self.incompleteResponses = 0
        self.OutputFolder = "OutputTest/"
        self.JSONFile = self.OutputFolder + "RunningLogs.json"
        self.CasesJSONFile = self.OutputFolder + "Cases.json"
        self.logsDf = pd.DataFrame()
        self.casesDf = pd.DataFrame()
        self.LOGGING = True
        self.fewshotsnum = 3
        self.isFewShot = True

    def generate(self, sI, eI):
        """
        This function is responsible for generating the test cases and running them
        It is the core of the TestGenerator class. It is responsible for:
        1. Extracting the code and description from the example
        2. Generating the test cases
        3. Running the test cases
        4. Storing the results in a JSON file
        Args: None
        Return: None
        """
        self.checkPaths()
        self.reset()
        FileHandle = open(self.OutputFolder + "Cases.txt", "w+")
        for i in range(sI, eI):
            # if (i == 107): 
            #     x = 2
            print("Running Test Case ", i)
            FileHandle.write(
                "Running Test Case "
                + str(i)
                + "\n=====================================\n"
            )
            # description and code from database
            code, description = self.extractInfo(i)
            fewShotStr = self.extractFewShots(code)
            try:
                unittest = self.GenUnitTestChain.invoke(
                    {
                        "description": description,
                        "code": code,
                        "test_cases_of_few_shot": "",  # few shot str empty till RAG is implemented
                    }
                )  # ,"test_cases_of_few_shot":fewShotStr
            except Exception as e:
                print("ERROR in invoking GenUnitTestChain")
                self.apiErrors += 1
                print(e)
                FileHandle.write("Test Case " + str(i) + " Didn't Run Due to Errorr\n=====================================\n")
                newRow = pd.DataFrame(
                    {
                        "CaseNumber": i,
                        "Description": description,
                        "Code": code,
                        "GeneratedCode": None,
                        "CodeRan": None,
                        "Feedback": None,
                        "FullFeedback": None,
                    },
                    index=[0],
                )
                # df = df.append(newRow, ignore_index=True)
                self.logsDf = pd.concat([self.logsDf, newRow])
                # Save the updated DataFrame back to the excel file using 'openpyxl' engine for writing
                jsondata = self.logsDf.to_dict(orient="records")
                with open(self.JSONFile, "w") as f:
                    json.dump(jsondata, f, indent=4)
                continue
            
            if (self.interfaceModerator == "LLama"):
                unittestCode, isIncompleteResponse = getCodeFromResponse(unittest.text, 0)
            elif (self.interfaceModerator == "HF"):
                unittestCode, isIncompleteResponse = getCodeFromResponse(unittest, 0)
            else:
                unittestCode, isIncompleteResponse = getCodeFromResponse(unittest["text"], 0)

            if isIncompleteResponse:
                self.incompleteResponses += 1
                print( "Test Case " + str(i) + " Didn't Run Due to Incomplete Response\n=====================================\n")
                FileHandle.write( "Test Case " + str(i) + " Didn't Run Due to Incomplete Response\n=====================================\n")
            
            feedback, feedbackparsed, codeTobeRun = self.runTest(code, unittestCode)

            # print(feedbackparsed)
            # feedback = "timed out"
            # feedbackparsed = None
            # if (feedback == "timed out") or (feedback == "API Error"):
            #     pass

            NonSucceedingCasesNames = getNonSucceedingTestcases(feedback)

            NonSucceedingCasesNamesList = (
                NonSucceedingCasesNames["failed"] + NonSucceedingCasesNames["error"]
            )
            
            self.writeResults(
                feedback,
                feedbackparsed,
                unittestCode,
                FileHandle,
                NonSucceedingCasesNamesList,
                i,
            )
            testsToRepeat = getEachTestCase(unittestCode, NonSucceedingCasesNamesList)
            

            self.descriptions.append(description)
            self.codes.append(code)
            self.resCodes.append(unittestCode)
            self.feedbacks.append(feedbackparsed)  # feedbackparsed
            # codeRanList.append(codeTobeRun)
            newRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Description": description,
                    "Code": code,
                    "GeneratedCode": unittestCode,
                    "CodeRan": codeTobeRun,
                    "Feedback": feedbackparsed,
                    "FullFeedback": feedback,
                    "TestsToRepeat": testsToRepeat,
                },
                index=[0],
            )
            self.logsDf = pd.concat([self.logsDf, newRow])
            # Save the updated DataFrame back to the excel file using 'openpyxl' engine for writing
            jsondata = self.logsDf.to_dict(orient="records")
            with open(self.JSONFile, "w") as f:
                json.dump(jsondata, f, indent=4)
        FileHandle.close()

        self.printResults()
        return

    def extractInfo(self, i):
        """
        Extract the description and code from the example in addition to prepending the function header
        Args: i (int): The index of the example in the JSON file
        Return: description (str): The description of the example
                code (str): The code of the example
        """
        if self.isHumanEval:
            description = self.data_JsonObj.iloc[i]["text"]
            code = self.data_JsonObj.iloc[i]["canonical_solution"]
            # remove initial spaces in extracted code
            code = code.strip()
            # extract the function definition and utility code
            funcDefiniton = self.data_JsonObj.iloc[i]["prompt"]
            funcDefiniton, Utility = getFunctionName(
                funcDefiniton
            )  # does not need entry point at the end of the day
            code = Utility + "\n" + funcDefiniton + code
            return code, description
        else:
            # example = self.data_JsonObj.iloc[i][0]
            # code = example["code_tokens"]
            # # preprocess it in form of function and replace all input() statements
            # code = replace_input(code)
            # # code = example[0]["code_tokens"]
            # description = example["description"]
            # # description = example[0]["description"]
            code = self.data_JsonObj.iloc[i]["AlteredCleanedCode"]
            # exclude last 3 letters
            code = code[:-3]
            description = self.data_JsonObj.iloc[i]["Description"]
            return code, description

    def extractFewShots(self, code):
        """
        Extract the few shot code and test cases from the database
        Args: code (str): The code of the example
        Return: fewShotStr (str): The few shot code and test cases
        """
        # get the number of shots from the environment variables and cast it to an integer
        fewshotsnum = int(os.getenv("FEWSHOTS"))
        # print(fewshotsnum)
        # print(type(fewshotsnum))
        # get the few shot code and test cases
        codeOfFewShots, testCasesFewShots = getFewShots(self.db, code)
        # take the most similar few shot other than the code itself
        codeOfFewShots = codeOfFewShots[0 : fewshotsnum]
        testCasesFewShots = testCasesFewShots[0 : fewshotsnum]
        fewShotStr = preprocessStringFewShot(codeOfFewShots, testCasesFewShots)
        return fewShotStr

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

    # def extractExampleInfo(self, example):
    #     # Extract the code and description from the example
    #     code = example["code"]
    #     description = example["description"]
    #     return code, description

    def runTest(self, code, unittestCode):
        """
        Run the test case after some preprocessing of the returned response
        """
        unittestCode = preprocessUnitTest(unittestCode)
        codeTobeRun = getRunningCode(code, unittestCode)
        feedback = ""
        try:
            feedback = runCode(codeTobeRun, self.myglobals)
            pass
        except KeyboardInterrupt:
            feedback = "timed out"

        if feedback == "timed out":
            feedbackparsed = "FAIL: 7; ERROR: 0"
            return feedback, feedbackparsed, codeTobeRun
        
        feedbackparsed = getFeedbackFromRun(feedback)
        return feedback, feedbackparsed, codeTobeRun

    def writeResults(
        self,
        feedback,
        feedbackparsed,
        unittestCode,
        FileHandle,
        NonSucceedingCasesNamesList,
        i,
    ):
        """
        Responsible for writing results to cases.txt and cases.json

        Args: feedbackparsed (str): The parsed feedback from the test case


        """
        numOfAssertions = getNumAssertions(unittestCode)
        if feedbackparsed == "" or feedbackparsed is None: # that means that the test case is OK
            # in case of OK
            self.successfulExamplesNum += 1
            self.OKCases += 1
            print(
                f"Test example {i} succeeded\n======================================\n"
            )
            print("Number of Ran Tests : ", numOfAssertions)
            print("Number of Succeeded Test : ", numOfAssertions)
            # print("Number of Succeeded Test : ", 0)
            FileHandle.write("Test example " + str(i) + " succeeded\n")
            FileHandle.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
            FileHandle.write(
                "Number of Succeeded Test : " + str(numOfAssertions) + "\n"
            )
            newCaseRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Total Tests": numOfAssertions,
                    "Tests failed": 0,
                    "Error Tests": 0,
                    "Old Total Tests": 0,
                    "Old Tests Failed": 0,
                    "Old Tests Error": 0,
                },
                index=[0],
            )

            self.casesDf = pd.concat([self.casesDf, newCaseRow])
            casejsondata = self.casesDf.to_dict(orient="records")
            with open(self.CasesJSONFile, "w") as f:
                json.dump(casejsondata, f, indent=4)

            self.totalTestCasesNum += numOfAssertions

        else:
            self.failedExamplesNum += 1
            if (feedback == "timed out"): feedback = f"failures={numOfAssertions}; errors=0"
            failedCasesNum, errorCasesNum = getNumNonSucceedingTestcases(feedback)
            # NonSucceedingCasesNames = getNonSucceedingTestcases(feedback)
            # NonSucceedingCasesNamesList = (
            #     NonSucceedingCasesNames["failed"] + NonSucceedingCasesNames["error"]
            # )
            # testsToRepeat = getEachTestCase(unittestCode, NonSucceedingCasesNamesList)
            numberOfSucceeded = numOfAssertions - failedCasesNum - errorCasesNum
            print(f"Test example {i} failed\n======================================\n")
            print("Number of Ran Tests : ", numOfAssertions)
            print("Number of failed Tests : ", failedCasesNum)
            print("Number of error Tests : ", errorCasesNum)
            print(
                "Number of Succeeded Test : ",
                numberOfSucceeded,
            )
            FileHandle.write("Test example " + str(i) + " failed\n")
            FileHandle.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
            FileHandle.write("Number of failed Tests : " + str(failedCasesNum) + "\n")
            FileHandle.write("Number of Error Test : " + str(errorCasesNum) + "\n")
            FileHandle.write(
                "Number of Succeeded Test : " + str(numberOfSucceeded) + "\n"
            )
            newCaseRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Total Tests": numOfAssertions,
                    "Tests failed": failedCasesNum,
                    "Error Tests": errorCasesNum,
                    "Old Total Tests": 0,
                    "Old Tests Failed": 0,
                    "Old Tests Error": 0,
                },
                index=[0],
            )

            self.casesDf = pd.concat([self.casesDf, newCaseRow])
            casejsondata = self.casesDf.to_dict(orient="records")
            with open(self.CasesJSONFile, "w") as f:
                json.dump(casejsondata, f, indent=4)
            self.testsToRepeatNum += len(NonSucceedingCasesNamesList)
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
        print("Incomplete Responses are : ", self.incompleteResponses)
        print("Incomplete Responses are ", self.incompleteResponses)
        print("API Errors are : ", self.apiErrors)
        print("Tests to repeat : ", self.testsToRepeatNum)
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
            f.write("Tests to repeat : " + str(self.testsToRepeatNum) + "\n")
