from Imports import *
from utils.CustomThread import *

from huggingface_hub import InferenceClient
from typing import Dict
from prompts_text import *
from llama_index.core import PromptTemplate



class TestFix:

    def __init__( self, UnitTestFeedbackChain, firstFeedback, myglobals):
        self.reset()
        self.UnitTestFeedbackChain = UnitTestFeedbackChain
        self.myglobals = myglobals
        self.firstFeedback = firstFeedback
        self.interfaceModerator = "HF"
        

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
        self.OutputFolder = "FeedbackOutput/"
        self.JSONFile = self.OutputFolder + "RunningLogs.json"
        self.CasesJSONFile = self.OutputFolder + "Cases.json"
        OldGeneratedTestsFolder = "OutputTest/"
        self.OldCasesFile = OldGeneratedTestsFolder + "Cases.json"
        self.OldJsonFile = OldGeneratedTestsFolder + "RunningLogs.json"
        self.CasesLogs = pd.read_json(self.OldJsonFile)
        self.OldCases = pd.read_json(self.OldCasesFile)
        self.logsDf = pd.DataFrame()
        self.casesDf = pd.DataFrame()
        self.firstFeedback = True

    def generate(self, startIndex):
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
        # print(self.firstFeedback)
        
        self.checkPaths()
        self.reset()
        FileHandle = open(self.OutputFolder + "Cases.txt", "w+")
        for i in range(len(self.CasesLogs)):
            print("********************************************************************")
            print("Running Example ", i + startIndex, "\n=====================\n")

            # Extract the description and code from the example
            currDescription, currCode, currGeneratedCode, currFeedback = self.extractInfo(i)
            
            # no feedback means testcase passed so don't run it again
            if ("OK" in currFeedback or pd.isna(currFeedback) or currFeedback == "" or currFeedback is None ):
                print("Example", i + startIndex, " has already passed")
                FileHandle.write( "Example " + str(i + startIndex) + " has already passed\n=====================================\n")
                continue
            
            try:
                # if (self.interfaceModerator == "HF"):
                #     client = InferenceClient(
                #         model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                #         token="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",
                #     )
                #     # def inferFun(prompt):
                #         # response = ""
                #     qa_template = PromptTemplate(RegenerateTestTemplate)

                #     prompt = qa_template.format(description=currDescription, code=currCode, UnitTests=currGeneratedCode, Feedback=currFeedback)

                #     GenerationPostFeedback = ""
                #     for message in client.chat_completion(
                #         messages=[{"role": "user", "content": prompt}],
                #         max_tokens=28_500,
                #         stream=True,
                #         temperature=0.1,
                #         # top_p = 0.6,
                #         ):
                        
                #         GenerationPostFeedback += message.choices[0].delta.content
                    
                # else:
                GenerationPostFeedback = self.UnitTestFeedbackChain.invoke(
                    {
                        "description": currDescription,
                        "code": currCode,
                        "UnitTests": currGeneratedCode,
                        "Feedback": currFeedback,
                    }
                )
            except Exception as e:
                print("ERROR in invoking Feedback Chain")
                self.apiErrors += 1
                print(e)
                FileHandle.write( "Example " + str(i + startIndex) + " Didn't Run Due to Errorr\n=====================================\n")
                continue
            # except KeyboardInterrupt as e:
            #     print(e)
            #     print("Keyboard Interrupt")
            #     FileHandle.write(
            #         "Example "
            #         + str(i)
            #         + " Didn't Run Due to Error\n=====================================\n"
            #     )
            #     continue

            if (self.interfaceModerator == "LLama"):
                newUnitTestCode, isIncompleteResponse = getCodeFromResponse(GenerationPostFeedback.text, 1)
            elif (self.interfaceModerator == "HF"):
                newUnitTestCode, isIncompleteResponse = getCodeFromResponse(GenerationPostFeedback, 1)
            else:
                newUnitTestCode, isIncompleteResponse = getCodeFromResponse(GenerationPostFeedback["text"], 1)
            

            
            if isIncompleteResponse:
                self.incompleteResponses += 1
                print(
                    "Test Case "
                    + str(i + startIndex)
                    + " Didn't Run Due to Incomplete Response\n=====================================\n"
                )
                FileHandle.write(
                    "Example "
                    + str(i + startIndex)
                    + " Didn't Run Due to Incomplete Response\n=====================================\n"
                )

            unittestCode = preprocessUnitTest(newUnitTestCode)
            codeTobeRun = getRunningCode(currCode, unittestCode)
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
                FileHandle,
                NonSucceedingCasesNamesList,
                i,
                i + startIndex
            )
            self.descriptions.append(currDescription)
            self.codes.append(currCode)
            self.resCodes.append(unittestCode)
            self.feedbacks.append(feedbackparsed)  # feedbackparsed
            # codeRanList.append(codeTobeRun)
            newRow = pd.DataFrame(
                {
                    "CaseNumber": i + startIndex,
                    "Description": currDescription,
                    "Code": currCode,
                    "GeneratedCode": unittestCode,
                    "CodeRan": codeTobeRun,
                    "Feedback": feedbackparsed,
                    "FullFeedback": feedback,
                    "TestsToRepeat": testsToRepeat,
                },
                index=[0],
            )
            
            # df = df.append(newRow, ignore_index=True)
            self.logsDf = pd.concat([self.logsDf, newRow])
            jsondata = self.logsDf.to_dict(orient="records")
            with open(self.JSONFile, "w") as f:
                json.dump(jsondata, f, indent=4)

        self.printResults()
        FileHandle.close()
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
        currGeneratedCode = self.CasesLogs.iloc[i]["GeneratedCode"]
        currFeedback = self.CasesLogs.iloc[i]["Feedback"]

        return currDescription, currCode, currGeneratedCode, currFeedback

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
        self,
        feedback,
        feedbackparsed,
        unittestCode,
        FileHanlde,
        NonSucceedingCasesNamesList,
        i,
        virtualIndex # the index that is attributed to the whole dataset
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
                f"Test example {virtualIndex} succeeded\n======================================\n"
            )
            print("Number of Ran Tests : ", numOfAssertions)
            print("Number of Succeeded Test : ", numOfAssertions)
            print("Number of Succeeded Test : ", 0)
            FileHanlde.write("Test example " + str(virtualIndex) + " succeeded\n")
            FileHanlde.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
            FileHanlde.write(
                "Number of Succeeded Test : " + str(numOfAssertions) + "\n"
            )

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
                    "CaseNumber": virtualIndex,
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
                    f"Test example {virtualIndex} failed due to syntax or indentation or timeout\n======================================\n"
                )
                print("Number of Ran Tests : ", 0)
                print("Number of failed Tests : ", 0)
                print("Number of error Tests : ", 1)
                print("Number of Succeeded Test : ", 0)
                FileHanlde.write(
                    "Test example "
                    + str(virtualIndex)
                    + " failed due to syntax or indentation or timeout\n"
                )
                FileHanlde.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
                FileHanlde.write("Number of failed Tests : " + str(0) + "\n")
                FileHanlde.write("Number of Error Test : " + str(1) + "\n")
                FileHanlde.write("Number of Succeeded Test : " + str(0) + "\n")
                self.failedExamplesNum += 1
                return
            self.failedExamplesNum += 1
            failedCasesNum, errorCasesNum = getNumNonSucceedingTestcases(feedback)
            numberOfSucceeded = numOfAssertions - failedCasesNum - errorCasesNum
            print(f"Test example {virtualIndex} failed\n======================================\n")
            print("Number of Ran Tests : ", numOfAssertions)
            print("Number of failed Tests : ", failedCasesNum)
            print("Number of error Tests : ", errorCasesNum)
            print(
                "Number of Succeeded Test : ",
                numberOfSucceeded,
            )
            FileHanlde.write("Test example " + str(virtualIndex) + " failed\n")
            FileHanlde.write("Number of Ran Tests : " + str(numOfAssertions) + "\n")
            FileHanlde.write("Number of failed Tests : " + str(failedCasesNum) + "\n")
            FileHanlde.write("Number of Error Test : " + str(errorCasesNum) + "\n")
            FileHanlde.write(
                "Number of Succeeded Test : " + str(numberOfSucceeded) + "\n"
            )

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
                    "CaseNumber": virtualIndex,
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
            self.totalTestCasesNum += numOfAssertions
            self.testsToRepeat += len(NonSucceedingCasesNamesList)
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
        print("API Errors are : ", self.apiErrors)
        print("Incomplete Responses are ", self.incompleteResponses)
        print("Tests to repeat : ", self.testsToRepeat)
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
