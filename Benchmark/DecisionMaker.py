from Imports import *
from utils.CustomThread import *


class DecisionMaker:

    def __init__(self, JudgeChain, myglobals):
        self.reset()
        self.JudgeChain = JudgeChain
        # self.db = db
        self.myglobals = myglobals

    def reset(self):
        self.apiErrors = 0
        self.TotalExamples = 0
        self.incompleteResponses = 0
        self.codes = []
        self.judgementsCodeBuggy = []
        self.judgementsTestBuggy = [] 
        self.explanations = []
        self.descriptions = []
        self.OutputFolder = "JudgeOutput/"
        self.JSONFile = self.OutputFolder + "JudgmentLogs.json"
        ###############
        OldGeneratedTestsFolder = "OutputTest/"
        self.OldCasesFile = OldGeneratedTestsFolder + "Cases.json"
        self.OldJsonFile = OldGeneratedTestsFolder + "RunningLogs.json"
        self.CasesLogs = pd.read_json(self.OldJsonFile)
        self.OldCases = pd.read_json(self.OldCasesFile)
        # running logs
        self.logsDf = pd.DataFrame()
        self.LOGGING = True

    def generate(self):
        """
        This function is responsible for generating the test cases and running them
        It is the core of the DecisionMaker class. It is responsible for:
        1. Extracting the code and description from the example
        2. Generating the test cases
        3. Running the test cases
        4. Storing the results in a JSON file
        Args: None
        Return: None
        """
        self.checkPaths()
        self.reset()
        FileHandle = open(self.OutputFolder + "Cases.txt", "w+", encoding='utf-8')
        for i in range(len(self.CasesLogs)):
            if i == 3:
                continue
            print("Running Test Case ", i)
            FileHandle.write(
                "Running Test Case "
                + str(i)
                + "\n=====================================\n"
            )
            # description and code from database
            description, code, errorMsg, errorTestCases = self.extractInfo(i)
            # fewShotStr = self.extractFewShots(code)
            if (
                "OK" in errorMsg
                or pd.isna(errorMsg)
                or errorMsg == ""
                or errorMsg is None
            ):
                print("Example", i, " has already passed")
                FileHandle.write(
                    "Example "
                    + str(i)
                    + " has already passed\n=====================================\n"
                )
                continue
            try:
                errorMsg = getOneError(errorMsg)
                generatedJudgement = self.JudgeChain.invoke(
                    {
                        "code": code,
                        "description": description,
                        # "test_cases_of_few_shot": fewShotStr,
                        "test_case_error": errorTestCases,
                        "error_message": errorMsg,
                    }
                )  # ,"test_cases_of_few_shot":fewShotStr
            except Exception as e:
                print("ERROR in invoking JudgeChain")
                self.apiErrors += 1
                print(e)
                FileHandle.write(
                    "Test Case "
                    + str(i)
                    + " Didn't Run Due to Errorr\n=====================================\n"
                )
                newRow = pd.DataFrame(
                    {
                        "CaseNumber": i,
                        "Description": description,
                        "Code": code,
                        "JudgementCodeBuggy": None,
                        "JudgementTestBuggy": None,
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

            print("generatedJudgement: ", generatedJudgement["text"])
            try:
                FileHandle.write(
                    "generatedJudgement: " + str(generatedJudgement["text"]) + "\n"
                )
            except Exception as e:
                print("Error in writing to file")
                print(e)

            judgementCodeBuggy,judgementTestBuggy, explanation, isIncompleteResponse = getJudgmentFromGeneration(
                generatedJudgement["text"]
            )
            if isIncompleteResponse:
                self.incompleteResponses += 1
                print(
                    "Test Case "
                    + str(i)
                    + " Didn't Run Due to Incomplete Response\n=====================================\n"
                )
                FileHandle.write(
                    "Test Case "
                    + str(i)
                    + " Didn't Run Due to Incomplete Response\n=====================================\n"
                )
            self.TotalExamples += 1
            self.writeResults(
                judgementCodeBuggy,
                judgementTestBuggy,
                explanation,
                FileHandle,
                i,
            )
            self.descriptions.append(description)
            self.codes.append(code)
            self.judgementsCodeBuggy.append(judgementCodeBuggy)
            self.judgementsTestBuggy.append(judgementTestBuggy)
            self.explanations.append(explanation)
            # codeRanList.append(codeTobeRun)
            newRow = pd.DataFrame(
                {
                    "CaseNumber": i,
                    "Description": description,
                    "Code": code,
                    "JudgementCodeBuggy": judgementCodeBuggy,
                    "JudgementTestBuggy": judgementTestBuggy,
                    "Explanation": explanation,
                    "TestCaseError": errorTestCases,
                    "ErrorMessage": errorMsg,
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
                generatedCode (str): The generated code of the example
                feedback (str): The feedback of the example
        """
        currCode = self.CasesLogs.iloc[i]["Code"]
        currDescription = self.CasesLogs.iloc[i]["Description"]
        currFeedback = self.CasesLogs.iloc[i]["Feedback"]
        errorTestCases = self.CasesLogs.iloc[i]["TestsToRepeat"]
        # generatedTestCases = self.CasesLogs.iloc[i]["GeneratedCode"]

        return currDescription, currCode, currFeedback, errorTestCases

    def extractFewShots(self, code):
        """
        Extract the few shot code and test cases from the database
        Args: code (str): The code of the example
        Return: fewShotStr (str): The few shot code and test cases
        """
        # get the few shot code and test cases
        codeOfFewShots, testCasesFewShots = getFewShots(self.db, code)
        # take the most similar few shot other than the code itself
        codeOfFewShots = codeOfFewShots[1:4]
        testCasesFewShots = testCasesFewShots[1:4]
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

        if not os.path.exists(self.JSONFile):
            try:
                # Create a new empty JSON file with an empty list structure
                with open(self.JSONFile, "w") as f:
                    json.dump([], f)
                    print(f"File {self.JSONFile} created successfully!")
            except Exception as e:
                print(f"Error creating file {self.JSONFile}: {e}")
                exit()

    def extractExampleInfo(self, example):
        # Extract the code and description from the example
        code = example["code"]
        description = example["description"]
        return code, description

    def runTest(self, code, unittestCode):
        """
        Run the test case after some preprocessing of the returned response
        """
        unittestCode = preprocessUnitTest(unittestCode)
        codeTobeRun = getRunningCode(code, unittestCode)
        feedback = runCode(codeTobeRun, self.myglobals)
        feedbackparsed = getFeedbackFromRun(feedback)
        return feedback, feedbackparsed, codeTobeRun

    def writeResults(
        self,
        judgementCodeBuggy,
        judgementTestBuggy,
        explanation,
        FileHandle,
        i,
    ):
        """
        Responsible for writing results to cases.txt and cases.json

        Args: feedbackparsed (str): The parsed feedback from the test case


        """
        print(f"Test example {i} Judgement\n======================================\n")
        booljudgementCode = 1 if judgementCodeBuggy == "True" else 0
        finaljudgeCode = "Code is buggy " if booljudgementCode == 1 else "Code is correct"
        booljudgementTest = 1 if judgementTestBuggy == "True" else 0
        finaljudgeTest = "Test is buggy " if booljudgementTest == 1 else "Test is correct"
        print("Judgement Code : ", finaljudgeCode)
        print("Judgement Test : ", finaljudgeTest)
        print("Explanation : ", explanation)
        FileHandle.write("Test example " + str(i) + " failed\n")
        FileHandle.write("Judgement Code : " + finaljudgeCode + "\n")
        FileHandle.write("Judgement Test :  " + finaljudgeTest + "\n")
        FileHandle.write("Explanation " + str(explanation) + "\n")

    def printResults(self):
        """
        Prints the remaining results and create Res.txt which includes a summary of the overall run

        """
        print("\n End of Test Cases \n")
        print("Total  Examples : ", self.TotalExamples)
        print("Incomplete Responses are : ", self.incompleteResponses)
        print("API Errors are : ", self.apiErrors)
        print("Incomplete Responses are ", self.incompleteResponses)
        with open(self.OutputFolder + "Res.txt", "w") as f:
            f.write("Total examples : " + str(self.TotalExamples) + "\n")
            f.write(
                "Incomplete Responses are : " + str(self.incompleteResponses) + "\n"
            )
            f.write("API Errors are : " + str(self.apiErrors) + "\n")
