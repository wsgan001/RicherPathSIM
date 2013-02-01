from collections import defaultdict
import itertools
from src.similarity.MetaPathSimilarityStrategy import MetaPathSimilarityStrategy

__author__ = 'jontedesco'

class SimRankStrategy(MetaPathSimilarityStrategy):
    """
      Class that computes SimRank-based similarity scores
    """

    C = 0.8
    k = 20

    def __init__(self, graph, metaPath, symmetric = False):
        super(SimRankStrategy, self).__init__(graph, metaPath, symmetric)
        self.similarityScores = None


    def findSimilarityScore(self, source, destination):
        """
          Find the similarity score between two nodes
        """


        if self.similarityScores is not None:
            return self.similarityScores[source][destination]

        # Project graph
        if self.metaPath[0] == self.metaPath[-1]: # Homogeneous projection?
            projectedGraph = self.metaPathUtility.createHomogeneousProjection(self.graph, self.metaPath)
        else:
            projectedGraph = self.metaPathUtility.createHeterogeneousProjection(self.graph, self.metaPath)

        self.similarityScores = defaultdict(dict)
        nodes = self.graph.getNodes()
        for a, b in itertools.product(nodes, nodes):
            self.similarityScores[a][b] = 1 if a is b else 0

        self.similarityScores = self.__simRank(projectedGraph, self.similarityScores, SimRankStrategy.k)

        return self.similarityScores[source][destination]


    def __simRank(self, projectedGraph, previousSimilarities, iterationsRemaining):
        """
          Recursively compute the sim-rank of two nodes given the previous pairwise similarities of nodes in the graph

            @param  previousSimilarities    A 2-d dictionary of similarities between pairs of nodes
            @param  iterationsRemaining   The number of iterations remaining for simRank
        """

        if iterationsRemaining == 0:
            return previousSimilarities

        newSimilarities = defaultdict(dict)
        nodes = projectedGraph.getNodes()
        for a, b in itertools.product(nodes, nodes):

            if a is b:
                newSimilarities[a][b] = 1.0
            else:
                aNeighbors, bNeighbors = projectedGraph.getPredecessors(a), projectedGraph.getPredecessors(b)
                total = sum([previousSimilarities[aNeighbor][bNeighbor] for aNeighbor, bNeighbor in itertools.product(aNeighbors, bNeighbors)])
                total *= SimRankStrategy.C / float(len(aNeighbors) * len(bNeighbors))

                newSimilarities[a][b] = total

        return self.__simRank(projectedGraph, newSimilarities, iterationsRemaining - 1)

