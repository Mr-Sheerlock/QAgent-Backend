from Imports import *


load_dotenv()
MODEL = os.getenv("MODEL")
# model_name = "bigcode/starcoder2-15b"
model_name = "google/gemma-7b-it"
model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1"


max_new_tokens = 6000
if "Mixtral" in model_name:
    max_new_tokens = 29_100

# if (MODEL == "GPT-3.5-turbo"):
#     llm, chat_model = InitializeGptModel(
#         os.environ["OPENAI_API_KEY"], model_name, max_new_tokens=max_new_tokens
#     )
#     # queryGptGenerateTest()
# else:
#     llm, chat_model = InitializeModel(
#         os.environ["HUGGINGFACEHUB_API_TOKEN"], model_name, max_new_tokens=max_new_tokens
#     )
#     GenUnitTestChain = InitializeTestChain(llm, True)

### Re-initialize the model for the other chains
GenUnitTestChain = HFCustomInferenceAPI()
UnitTestFeedbackChain = HFCustomInferenceAPI()
llamaBugFix = HFCustomInferenceAPI()

# Generate Unit Tests
GenUnitTestChain.InitializeModel(os.environ["HUGGINGFACEHUB_API_TOKEN"], model_name, max_new_tokens, 1)

# UnitTestFeedbackChain = InitializeFeedbackChain(llm)
UnitTestFeedbackChain.InitializeModel(os.environ["HUGGINGFACEHUB_API_TOKEN"], model_name, max_new_tokens, 2)


# judgeChain = InitializeModel(llm)

# bugFixChain = InitializeModel(llm)


HEval_JsonObj = pd.read_json(path_or_buf="Datasets/humaneval.jsonl", lines=True)

db = connectDB()
