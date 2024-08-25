from vul_detection.vul_main import *
from flask_cors import CORS  # import flask_cors
from flask import Flask, request, jsonify
app = Flask(__name__)
# from Pipeline_Interface import QAgent_product
from Configuration import *
# from MainFunctions.TestGenerator import *
# from MainFunctions.TestFix import *
# from MainFunctions.DecisionMaker import *
# from MainFunctions.BugFix import *
from classical.main import main_for_api
# from SearchBasedBugFixing.bugFixLogic import *
# from DBRet.unixcoder import UniXcoder
# from DBRet.deploy import *
from DBRet.test import *
CORS(app)  # enable CORS

import subprocess

# # region QAgent
# def setupQAgent():
#     try:
#         print("All imports successful!")
#         testGenerator = TestGenerator(GenUnitTestChain, "", globals())
#         testRegenerator = TestFix(
#             UnitTestFeedbackChain,
#             globals(),
#             True,
#         )
#         judgeGenerator = DecisionMaker(judgeChain, globals())
#         bugFixGenerator = BugFix(bugFixChain, globals(), True)
#         return testGenerator, testRegenerator, bugFixGenerator, judgeGenerator
#     except Exception as e:
#         print(e)
#         exit(-1)


# testGenerator, testRegenerator, bugFixGenerator, judgeGenerator = setupQAgent()


# @app.route('/qagentai', methods=['POST'])
# def run_python():
#     code = request.json.get('code')
#     description = request.json.get('description')
#     if code:
#         try:
#             # execute the main function
#             print("Running QAgentAI")
#             result = QAgent_product(
#                 code, description, testGenerator, testRegenerator, bugFixGenerator, judgeGenerator)
#             # print(result)
#             return jsonify({'output': list(result)})
#         except Exception as e:
#             return jsonify({'error': str(e)}), 400
#     else:
#         return jsonify({'error': 'No code provided'}), 400

#endregion


@app.route('/query', methods=['POST'])
def query():
    try:
        print(request.json)
        code = request.json['code']
        programmingLangugae=request.json['language']
        print(programmingLangugae)
        if programmingLangugae=='python':
            isPython=True
            isJava=False
        elif programmingLangugae=='java':
            isPython=False
            isJava=True
        else:
            isPython=False
            isJava=False
        thresholdSameLanguage = request.json['thresholSameLang']
        thresholdDifferentLanguage = request.json['thresholdDiffLang']
        codes, tests = query_db(code,isJava,isPython,thresholdSameLanguage,thresholdDifferentLanguage)
        # print("codes is", codes)
        if len(codes) == 0:
            return jsonify({"codes":["No similar code found"], "tests": [{"test 0":"No similar code found"}]})
        return jsonify({'codes': codes, 'tests': tests})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/vuldetect', methods=['POST'])
def vulDetect():
    try:
        code = request.json['code']
        print(type(code))
        vuls = main_vul(code)
        return jsonify(vuls)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/run-classical', methods=['POST'])
def generate_classical():
    code = request.json.get('code')
    print(code)
    if code:
        # try:
            # execute the main function
        result = main_for_api(code)
        print(result)
        return jsonify({'output': result})
        # except Exception as e:
        #     return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'No code provided'}), 400

@app.route('/')
def hello():
    # print("looooooooooooooooooooooooooooooooooooooooooooooooooo")

    return 'hello man'


@app.route('/run-fixbugs', methods=['POST'])
def generate_fixbugs():
    # inputs = '[[1, 2],[3, 89]]'
    # outputs = '[[3], [92]]'
    # methodName = 'add'
    # code = 'def add(a, b): return a - b'
    # outputs = bugFix(code, methodName, inputs, outputs)
    # print(outputs)
    code = request.json.get('code')
    inputs = request.json.get('test_cases_inputs')
    # print(inputs)
    for i, input in enumerate(inputs):
        for j, inp in enumerate(input):
            if inputs[i][j].lower() == 'void':
                inputs[i][j] = 'void'
            else:
                inputs[i][j] = eval(inputs[i][j])
            
    outputs = request.json.get('test_cases_outputs')
    for i, output in enumerate(outputs):
        for j, inp in enumerate(output):
            outputs[i][j] = eval(outputs[i][j])
    
    # print(inputs)
    # print(outputs)
    function_name = request.json.get('function_name')
    # print(function_name)
    # print(code)
    if code:
        try:
            try:
                # result = subprocess.run(['ls'])
                result = subprocess.run(["python3", "/home/azureuser/GP/LLM-Test-Generator/SearchBasedBugFixing/main.py", str(code), str(function_name), str(inputs), str(outputs)], capture_output=True, text=True)
                # Access the stdout and stderr attributes of the result
                
                stdout = result.stdout
                print(stdout)
                stderr = result.stderr
                print(stderr)
                
                result = stdout
                # print(result)
            except subprocess.CalledProcessError as e:
                print("Error:", e)
            except Exception as e:
                print("Error:", e)
            
            print(result)
            if (result == ''):
                return jsonify({'output': 'No Fixes found'})
            return jsonify({'output': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'No code provided'}), 400


code = """def simple_function(x, y):
    query = "SELECT * FROM products WHERE id=" +  str(x) + " AND name='" + str(y) + "'"
    query += "'; DROP TABLE users; --"

    a = x + y
    os.system("echo Hello from the system!")
    if x == 0:
        print("x is zero!")
    b = x * y
    c = eval(input("Enter an expression: "))
    return a, b
 """
# print(main_vul(code))
# generate_fixbugs()

if __name__ == '__main__':
    # app.run(port=8080,debug=True, use_reloader=False)
    app.run(port=8000)

