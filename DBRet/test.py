import numpy as np
# from .unixcoder import UniXcoder
from .unixcoder import UniXcoder
import os
import json
import torch 
import faiss
from faiss import write_index, read_index
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

current_dir = os.path.dirname(__file__)

FaissIndexpathJ=os.path.join(current_dir,"catJava.index")
FaissIndexpathP=os.path.join(current_dir,"catPy.index")

Pindex=read_index(FaissIndexpathP)
Jindex=read_index(FaissIndexpathJ)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UniXcoder("microsoft/unixcoder-base")
model.to(DEVICE)

#returns numpy array of embeddings
def get_embeddings(model,tokens,device=DEVICE):
  tokens_ids = model.tokenize([tokens],max_length=512,mode="<encoder-only>")
  source_ids = torch.tensor(tokens_ids).to(device)
  _,embeddings = model(source_ids)
  return embeddings.detach()


# # Get the directory where Graph.py is located
# the files in the directory are named as test1.py, test2.py, test3.py, ... We sort according to number
# M2CodeFiles=sorted(M2CodeFiles, key=lambda x: int(re.search(r'\d+', x).group()))

CatlasCodeDirJ = os.path.join(current_dir, "catlasM2UniDedup")
CatlasCodeDirPy= os.path.join(current_dir, "catLMPyDedupUni")

def getClosestNeibours(query,index,k=3,threshold=0.8):
    
    similarities,indices=index.search(query,k)
    similarities=similarities[0]
    indices=indices[0]
    # [[10.980705 10.505952 10.488009]]
    # [[467623 467611 760859]]
    # [[10.980705 10.505952 10.488009]]
    # [[467623 467611 760859]]

    results=[]
    for sim,index in zip(similarities,indices):
        if sim>=threshold:
            results.append((index,sim))
    print(results)
    return results


def queryDB(query,k=3,isJava=True,isPython=True,thresholdSameLanguage=0.8,thresholdDifferentLanguage=0.6):
    global Jindex,Pindex
    if isJava:
        #give more priority to Java results
        idsAndDistancesJ=getClosestNeibours(query,Jindex,k,thresholdSameLanguage)
        idsAndDistancesP=[]
        # idsAndDistancesP=getClosestNeibours(query,Pindex,k-noOfJavaResults,Pindex,thresholdDifferentLanguage)
        
    elif isPython:
        #give more priority to Python results
        idsAndDistancesP=getClosestNeibours(query,Pindex,k,thresholdSameLanguage)
        idsAndDistancesJ=[]
    else:
        # sort the results based on similarity equally
        idsAndDistancesP=getClosestNeibours(query,Pindex,k,0.6)
        # add a flag for python
        idsAndDistancesP_python=[(res[0],res[1],0) for res in idsAndDistancesP]
        idsAndDistancesJ=getClosestNeibours(query,Jindex,k,0.8)
        # add a flag for java
        idsAndDistancesJ_Java=[(res[0],res[1],1) for res in idsAndDistancesP]
        
        idsAndDistances=idsAndDistancesP_python+idsAndDistancesJ_Java
        
        results=sorted(idsAndDistances,key=lambda x: 1-x[1])
        # classify each id based on the flag
        idsAndDistancesP=[]
        idsAndDistancesJ=[]
        for i in range(min(k,len(results))):
            if results[i][2]==0:
                idsAndDistancesP.append((results[i][0],results[i][1]))
            else:
                idsAndDistancesJ.append((results[i][0],results[i][1]))

    resultsJ=sorted(idsAndDistancesJ,key=lambda x: 1-x[1])
    JavaDB_ids=[res[0] for res in resultsJ[:k]]
    resultsP=sorted(idsAndDistancesP,key=lambda x: 1-x[1])
    PythonDB_ids=[res[0] for res in resultsP[:k]]

    
    global CatlasCodeDirPy,CatlasCodeDirJ
    codes=[]
    tests=[]
    for id in JavaDB_ids:
        # open json
        with open(os.path.join(CatlasCodeDirJ, f"test{id}.json")) as f:
            data = json.load(f)
            codes.append(data["code"])
            test=data["test_cases"]
            tests.append(test)
    for id in PythonDB_ids:
        # open json
        with open(os.path.join(CatlasCodeDirPy, f"test{id}.json")) as f:
            data = json.load(f)
            codes.append(data["code"])
            test=data["test_cases"]
            tests.append(test)

    return codes , tests

def query_db(code,isJava,isPython,thresholdSameLanguage=0.8,thresholdDifferentLanguage=0.6):
    
    global model, DEVICE, centroidsJ, centroidsP
    query = get_embeddings(model, code, DEVICE)
    query = torch.nn.functional.normalize(query,p=2, dim=1)
    query = query.numpy()
    codes,tests = queryDB(query , 3, isJava, isPython, thresholdSameLanguage, thresholdDifferentLanguage)
    return codes, tests


# code="lolxd"
# isJava=False
# isPython=False
# thresholdSameLanguage=0.8
# thresholdDifferentLanguage=0.6
# codes,tests=query_db(code,isJava,isPython,thresholdSameLanguage,thresholdDifferentLanguage)
# print(codes)
# print(tests)
# print(len(codes))
# print(len(tests))
