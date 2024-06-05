import random
import sys
sys.path.append("..") #
from Graph import Graph, Vertex
import numpy as np
import pandas as pd
import pickle
import os
import sys
from sklearn.cluster import DBSCAN, KMeans
from multiprocessing import Process, Queue, cpu_count, Pool


class VecDB:
    # TODO:
    # 2 Constructors:
    # VecDB() followed by db.insert_records(records_dict)
    # VecDB(file_path , new_db = False)
    # where file path is the path to the binary file having the index
    # retrieve(query, top_k)
    # L R
    # R > log n
    fiveKparams = (14, 15)
    tenKparams = (15, 17)
    hundredKparams = (20, 20)

    # file path of binary file
    def __init__(self, file_path="DBIndex10K/", new_db=True):
        # R= 17, L= 15, alpha = 2, K= 5,
        self.IndexPath = file_path
        if new_db:
            # TODO: Check the records per cluster here or at insert records
            self.L, self.R = VecDB.tenKparams
            self.n_clusters = 10
            if os.path.exists(self.IndexPath):
                print(
                    "Found existing files and their count is",
                    len(os.listdir(self.IndexPath)),
                )
        else:
            self.L, self.R = VecDB.hundredKparams
            self.n_clusters = 10
        self.alpha = 2
        self.offset = 0
        self.DBGraph = None
        self.currentfile = 0
        # medoids of all the clusters that we will get
        self.medoids = []

        # if(not new_db):
        #     # load graph from binary file
        #     #TODO: remove hard coded value
        #     self.DBGraph= pickle.load(open(file_path+"0.bin", "rb"))

    # TODO: CHECK after klam el mo3eed: might need to handle enk t4oof el directory
    # records are list of dictionaries containing id and embeddings
    def insert_records(self, records):

        # begin by clustering
        # records = np.array([[x["id"]] + x["embed"] for x in records])
        ids = np.array([x["id"] for x in records])
        embeddings = np.array([x["embed"] for x in records])
        # normalize records
        embeddings /= np.linalg.norm(embeddings, axis=1)[:, np.newaxis]
        print("Clustering...")
        # TODO: Remove random state later
        clustered_DB = KMeans(n_clusters=self.n_clusters, random_state=42).fit(
            embeddings
        )
        print("Finished Clustering...")
        # divide clustered_DB accoding to which label it was classsified
        for label in np.unique(clustered_DB.labels_):
            print("Inserting cluster ", label)
            indices = np.where(clustered_DB.labels_ == label)
            print("Number of records in cluster ", len(indices[0]))
            clusterIDs = ids[indices]
            clusterEmbeddings = embeddings[indices]
            # dists = []
            # for v1 in clusterEmbeddings:
            #     for v2 in clusterEmbeddings:
            #         dists.append(np.dot(v1, v2))
            # print(dists)

            self.DBGraph = self.Initialize_Random_Graph(clusterIDs, clusterEmbeddings)
            # hardcoded zero
            medoid = self.DBGraph.get_Medoid(0)
            self.medoids.append(medoid)
            self.DBGraph.medoid = medoid
            self.Build_Index()

            # handle directory doesn't exist
            if not os.path.exists(self.IndexPath):
                os.makedirs(self.IndexPath)

            # set current file to len of current files in director
            print("writing to ", self.IndexPath + str(self.currentfile) + ".bin")
            with open(self.IndexPath + str(self.currentfile) + ".bin", "wb") as f:
                pickle.dump(self.DBGraph, f)
            self.currentfile = len(os.listdir(self.IndexPath))

        # print("Done inserting, now Writing medoids ")
        with open(self.IndexPath + "medoids.bin", "wb") as f:
            pickle.dump(self.medoids, f)

    def load_binary_data(self, binary_file_path):
        # Load the data from the binary file
        with open(binary_file_path, "rb") as f:
            data = pickle.load(f)
        # offset of last inserted record
        self.offset = data.iloc[0][0]
        # print(data)
        return data

    # Initialize a Graph connected randomly from the given records
    # records is a list of dictionaries containing id and embeddings
    # the function also calls the graph to calculate its medoid
    def Initialize_Random_Graph(self, ids, records):
        DBGraph = Graph()
        for i in range(len(ids)):
            DBGraph.add_vertex(Vertex(ids[i], records[i]))

        size = len(DBGraph.verticies)
        if size == 0 or size == 1:
            return
        self.offset = ids[0]
        # Building Edges
        for vertex in DBGraph:
            # we want R neighbors
            for i in range(self.R):
                neighbor = DBGraph.get_vertex(np.random.choice(ids))
                while neighbor == vertex:
                    neighbor = DBGraph.get_vertex(np.random.choice(ids))
                DBGraph.add_edge(
                    (vertex.key, vertex.value), (neighbor.key, neighbor.value)
                )
        return DBGraph

    def index_to_distance(self, id, query):
        vertex = self.DBGraph.get_vertex(id)
        dist = self.get_distance(vertex.value, query)
        return dist

    # def Parallel_Files(self,file,query,k):
    def Parallel_Files(self, temp):
        # if ( filename[-3:] !="bin"):
        #     continue
        # filepath = os.path.join(self.IndexPath, filename)
        file, query, k = temp
        DBGraph = pickle.load(open(file, "rb"))
        V = VecDB()
        V.DBGraph = DBGraph

        TopK = V.Greedy_Search_Online(DBGraph.medoid, query, k)
        # ClustersResults.extend([(self.index_to_distance(VertexId, query), VertexId) for VertexId in TopK])
        ClustersResults = [
            (V.index_to_distance(VertexId, query), VertexId) for VertexId in TopK
        ]
        return ClustersResults  # assume filename is correctly labled
        # self.offset+=len(self.DBGraph.verticies)

    def retrieve(self, query, k):
        threads = cpu_count()
        # print("Number of cpus : ", threads)
        query /= np.linalg.norm(query)
        if query.shape[0] == 1:
            query = query[0]
        # top k from all clusters
        if len(self.medoids) == 0:
            self.medoids = pickle.load(open(os.path.join(self.IndexPath , "medoids.bin"), "rb"))

        noOfGraphs = 10
        if len(self.medoids) == 100:  # 1 million
            noOfGraphs = 20
        elif len(self.medoids) <= 1000:  # 10 million
            noOfGraphs = 25
        elif len(self.medoids) <= 1500:  # 10 million
            noOfGraphs = 27
        elif len(self.medoids) == 2000:  # 20 million
            noOfGraphs = 30
        # if k is larger than the number of files
        if noOfGraphs >= len(self.medoids):
            files = [os.path.join(self.IndexPath, str(i) + ".bin") for i in range(len(self.medoids))]
        else:
            distances = np.array(
                [self.get_distance(medoid.value, query) for medoid in self.medoids]
            )
            # sort indices according to distances
            sortedindices = np.argsort(distances)

            files = [
                self.IndexPath + str(i) + ".bin" for i in sortedindices[:noOfGraphs]
            ]
        # print(files)
        ClustersResults = []
        for filename in files:
            self.DBGraph = pickle.load(open(filename,"rb"))

            TopK= self.Greedy_Search_Online(self.DBGraph.medoid,query, k)
            ClustersResults.extend([(self.index_to_distance(VertexId, query), VertexId) for VertexId in TopK])
        ClustersResults.sort()
        ClustersResults = [element[1] for element in ClustersResults[:k]]
        return ClustersResults
        # self.offset+=len(self.DBGraph.verticies)
        # pool = Pool()
        # results = pool.map(self.Parallel_Files, [(i, query, k) for i in files])
        # results = [item for sublist in results for item in sublist]
        # FinalResults = results
        # FinalResults.sort()
        # FinalResults = [element[1] for element in FinalResults[:k]]
        # return FinalResults

    # gets euclidean distance between 2 vectors
    def get_distance(self, v1, v2):
        dist = np.dot(v1, v2)  # / (np.linalg.norm(v1) * np.linalg.norm(v2))
        # print(v1.shape, v2.shape)
        # added to avoid fp errors
        return max(min(1.0 - dist, 1), 0)
        # return  np.linalg.norm(v1-v2)

    def get_min_dist_Key(self, AnyKeysSet, Query):

        # put to 50 because the max distance is 2 anyway
        min_dist = 50
        min_vertex = None
        for vertexKey in AnyKeysSet:
            # print("vertex",vertex)
            # print("Query",Query[:3])
            vertex = self.DBGraph.get_vertex(vertexKey)
            dist = self.get_distance(vertex.value, Query)
            # print(dist)
            if dist < min_dist:
                min_dist = dist
                min_vertex = vertex.key
        return min_vertex, min_dist

    def Greedy_Search_Online(self, start, Query, k):
        search_List = {start.key}
        Visited = set()
        # TODO: make the visited and the possible frontier set of indices instead of vertices to save ram.
        possible_frontier = search_List
        Query /= np.linalg.norm(Query)
        while possible_frontier != set():
            # print('possible_frontier',possible_frontier)
            p_star, _ = self.get_min_dist_Key(possible_frontier, Query)

            search_List = search_List.union(self.DBGraph.get_vertex(p_star).neighbors)
            Visited.add(p_star)
            if len(search_List) > self.L:
                # update search list to retain closes L points to x_q
                search_ListL_L = list(search_List)
                search_ListL_L.sort(
                    key=lambda x: self.get_distance(
                        self.DBGraph.get_vertex(x).value, Query
                    )
                )
                # only maintain L closest points
                search_ListL_L = search_ListL_L[: self.L]
                search_List = set(search_ListL_L)

            possible_frontier = search_List.difference(Visited)

        search_ListL_L = list(search_List)
        search_ListL_L.sort(
            key=lambda x: self.get_distance(self.DBGraph.get_vertex(x).value, Query)
        )
        # only maintain k closest points
        search_ListL_L = search_ListL_L[:k]
        search_List = set(search_ListL_L)
        # both are vectors of integers
        return search_List

    # def Greedy_Search_Online(self,start,Query, k):
    # search_List={start.key}
    # Visited=set()
    # #TODO: make the visited and the possible frontier set of indices instead of vertices to save ram.
    # possible_frontier=search_List
    # Query /= np.linalg.norm(Query)
    # while possible_frontier != set():
    #     # print('possible_frontier',possible_frontier)
    #     p_star,_= self.get_min_dist_Key(possible_frontier,Query)

    #     search_List=search_List.union(self.DBGraph.get_vertex(p_star).neighbors)
    #     Visited.add(p_star)
    #     if(len(search_List)>self.L):
    #         #update search list to retain closes L points to x_q
    #         search_ListL_L=list(search_List)
    #         search_ListL_L.sort(key=lambda x: self.get_distance(self.DBGraph.get_vertex(x).value,Query))
    #         # only maintain L closest points
    #         search_ListL_L=search_ListL_L[:self.L]
    #         search_List=set(search_ListL_L)

    #     possible_frontier=search_List.difference(Visited)

    # search_ListL_L=list(search_List)
    # search_ListL_L.sort(key=lambda x: self.get_distance(self.DBGraph.get_vertex(x).value,Query))
    # # only maintain k closest points
    # search_ListL_L=search_ListL_L[:k]
    # search_List=set(search_ListL_L)
    # # both are vectors of integers
    # return search_List

    # initially, start is the medoid
    # s is a vertex, Query is a vector
    # k is a number, L is a number

    def Greedy_Search(self, start, Query, k):
        search_List = {start.key}
        Visited = set()
        # TODO: make the visited and the possible frontier set of indices instead of vertices to save ram.
        possible_frontier = search_List
        Query /= np.linalg.norm(Query)
        while possible_frontier != set():
            # print('possible_frontier',possible_frontier)
            p_star, _ = self.get_min_dist_Key(possible_frontier, Query)
            search_List = search_List.union(self.DBGraph.get_vertex(p_star).neighbors)
            Visited.add(p_star)
            if len(search_List) > self.L:
                # update search list to retain closes L points to x_q
                search_ListL_L = list(search_List)
                search_ListL_L.sort(
                    key=lambda x: self.get_distance(
                        self.DBGraph.get_vertex(x).value, Query
                    )
                )
                # only maintain L closest points
                search_ListL_L = search_ListL_L[: self.L]
                search_List = set(search_ListL_L)

            possible_frontier = search_List.difference(Visited)

        search_ListL_L = list(search_List)
        search_ListL_L.sort(
            key=lambda x: self.get_distance(self.DBGraph.get_vertex(x).value, Query)
        )
        # only maintain k closest points
        search_ListL_L = search_ListL_L[:k]
        search_List = set(search_ListL_L)
        # both are vectors of integers
        return search_List, Visited

    # # Robust pruning
    # candidate set is set of integers
    def Robust_Prune(self, point, candidate_set, alpha):
        # print(candidate_set)
        candidate_set = candidate_set.union(point.neighbors)
        candidate_set = candidate_set.difference({point.key})
        point.neighbors = set()

        while candidate_set:
            p_star, _ = self.get_min_dist_Key(candidate_set, point.value)
            point.neighbors.add(p_star)
            # if length is larger, I still want to prune
            if len(point.neighbors) == self.R:
                break
            DummySet = candidate_set.copy()

            for candidatePointKey in candidate_set:
                candidatePoint = self.DBGraph.get_vertex(candidatePointKey)
                if alpha * self.get_distance(
                    self.DBGraph.get_vertex(p_star).value, candidatePoint.value
                ) <= self.get_distance(candidatePoint.value, point.value):
                    DummySet.remove(candidatePoint.key)
            candidate_set = DummySet

    def Build_Index(self):

        # R = min(R, len(dataset))
        self.iterationOverGraph(1)  # alpha=1
        self.iterationOverGraph(self.alpha)  # alpha=2
        # self.iterationOverGraph(1.2)

    def iterationOverGraph(self, alpha):
        # print('medoid',medoid)
        randIndex = list(self.DBGraph.get_vertices())
        random.shuffle(randIndex)
        # random permutation + sequential graph update
        for n in randIndex:
            node = self.DBGraph.get_vertex(n)
            # print(n)

            (_, V) = self.Greedy_Search(self.DBGraph.medoid, node.value, 1)  # K=1
            self.Robust_Prune(node, V, alpha)

            neighbors = node.get_neighbors()

            for inbKey in neighbors:

                # CHECK : The backward edge is always added
                # check here in case we shouldn't add it in all cases ? Might be incorrect?
                inb = self.DBGraph.get_vertex(inbKey)
                if len(inb.get_neighbors()) > self.R:
                    # print("inb.get_neighbors()", inb.get_neighbors())
                    U = inb.get_neighbors().union({node.key})
                    # inb.add_neighbor(node.key)
                    self.Robust_Prune(inb, U, alpha)
                else:
                    inb.add_neighbor(node.key)