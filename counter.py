import pandas as pd

OldFile = "Results/FeedbackMixtral-1Shot/"
OldCasesFile = OldFile + "Cases.json"
OldCases = pd.read_json(OldCasesFile)
OlTotal = 0
OlFailTotal = 0
NowTotal = 0
NowFailTotal = 0
for i in range(len(OldCases)):
    OlTotal += OldCases.iloc[i]["Old Total Tests"]
    OlFailTotal += OldCases.iloc[i]["Old Tests Failed"]
    NowTotal += OldCases.iloc[i]["Feedback Total Tests"]
    NowFailTotal += OldCases.iloc[i]["Feedback Tests Failed"]

print("Old Total: ", OlTotal)
print("Old Fail Total: ", OlFailTotal)
print("Now Total: ", NowTotal)
print("Now Fail Total: ", NowFailTotal)
