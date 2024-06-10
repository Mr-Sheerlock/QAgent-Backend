import numpy as np
from .unixcoder import UniXcoder
import torch
import os
import json
import pickle
current_dir = os.path.dirname(__file__)

clustersPathJ=os.path.join(current_dir,'clustersJ256')
centroidsPathJ=os.path.join(clustersPathJ,'centroids.pkl')
centroidsJ= pickle.load(open(os.path.join(centroidsPathJ), 'rb'))

clustersPathP=os.path.join(current_dir,'clustersPy160')
centroidsPathP=os.path.join(clustersPathP,'centroids.pkl')
centroidsP= pickle.load(open(centroidsPathP, 'rb'))





def queryDB(query,centroids,clustersPath,noOfCentroidsSerached=30,k=3):
    distances=np.einsum('ac,bc->ab', query, centroids)[0]
    # pick the minimum 10 arguments from the distances
    clusterindices=np.argsort(distances)[-noOfCentroidsSerached:]
    results=[]
    # IDEA: change einsum arguments and replace the for loop with einsum
    for clusterindex in clusterindices:
        cluster=pickle.load(open(os.path.join(clustersPath,f'cluster{clusterindex}.pkl'), 'rb'))
        # res=cluster.query(query)
        dists=np.einsum('ac,bc->ab', query, cluster.vectors)[0]
        index=np.argmax(dists)
        resid=cluster.idx[index]
        dist=dists[index]
        if dist<threshold:
            
        results.append((resid,dist))
    results=sorted(results,key=lambda x: 1-x[1])
    db_ids=[res[0] for res in results[:k]]
    print(db_ids)

    codes=[]
    tests=[]
    ``
    return codes,tests

def query_db(code):
    global model, DEVICE,centroidsJ,centroidsP
    query = get_embeddings(model, code, DEVICE)
    query = query.numpy()
    # codes,tests=queryDB(query,centroidsJ,clustersPathJ)
    codesP,testsP=queryDB(query,centroidsP,clustersPathP,CatlasCodeDirPy)
    # distances=np.einsum('ac,bc->ab', query, centroidsJ)[0]
    # # pick the minimum 10 arguments from the distances
    # clusterindices=np.argsort(distances)[-30:]
    # results=[]
    # # IDEA: change einsum arguments and replace the for loop with einsum
    # for clusterindex in clusterindices:
    #     cluster=pickle.load(open(os.path.join(clustersPath,'cluster{}.pkl'.format(clusterindex)), 'rb'))
    #     # res=cluster.query(query)
    #     dists=np.einsum('ac,bc->ab', query, cluster.vectors)[0]
    #     index=np.argmax(dists)
    #     resid=cluster.idx[index]
    #     dist=dists[index]
    #     results.append((resid,dist))
    # results=sorted(results,key=lambda x: 1-x[1])
    # db_ids=[res[0] for res in results[:3]]
    # print(db_ids)

    # codes=[]
    # tests=[]
    # for id in db_ids:
    #     # open json
    #     with open(os.path.join(CatlasJCodeDir, f"test{id}.json")) as f:
    #         data = json.load(f)
    #         codes.append(data["code"])
    #         test=data["test_cases"]
    #         tests.append(test)
    #         # test=""
    #         # for testcase in data["test_cases"]:
    #         #     test+=testcase + '\n'
    return codesP,testsP
