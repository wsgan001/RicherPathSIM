import hashlib
import os
import cPickle

__author__ = 'jontedesco'

class MetaPathUtility(object):
    """
      Contains helper methods for dealing with meta paths. Note that this utility only handles meta paths that start and
      end at different nodes, and that never repeat nodes in the path (repeating meta path types is fine).
    """

    def findMetaPathNeighbors(self, graph, node, metaPath, symmetric = False, checkLoops = True):
        """
          Finds the neighbors of some node along the given meta path, i.e. nodes that are reachable from the given node
          along the given meta path.

            @param  graph       The graph in which to find meta path neighbors
            @param  node        The starting node for which to find neighbors
            @param  metaPath
        """

        # Verify that the given node is a valid starting node for the given meta path
        assert(node.__class__ == metaPath[0])

        # Get the paths & neighbors, then add this node if necessary
        (metaPathNeighbors, paths) = self._findMetaPathsHelper(graph, node, metaPath[1:], [], symmetric)
        if checkLoops:
            selfLoops = self.__findLoopMetaPaths(graph, node, metaPath, symmetric)
            if len(selfLoops) > 0:
                metaPathNeighbors.add(node)
        return set(metaPathNeighbors)


    def findMetaPaths(self, graph, startingNode, endingNode, metaPath, symmetric = False):
        """
          Finds all paths that match the metaPath connecting the given nodes
        """

        # Check that the endpoints are of the correct types
        assert(startingNode.__class__ == metaPath[0])
        assert(endingNode.__class__ == metaPath[-1])

        # Split logic based on whether or not the path should be a cycle
        if startingNode == endingNode:
            return self.__findLoopMetaPaths(graph, startingNode, metaPath, symmetric)
        else:
            return self.__findNonLoopMetaPaths(graph, startingNode, endingNode, metaPath, symmetric)


    def expandPartialMetaPath(self, partialMetaPath, repeatLastType = False):
        """
          Expands a partial meta path into a full one (i.e. ABC into ABCBA or ABCCBA)

            @param  partialMetaPath The partial meta path to expand
            @param  repeatLastType  Whether or not to repeat the last type in meta path expansion
                                    (i.e. should the final meta path be even length?)
        """

        reversedMetaPath = list(partialMetaPath)
        reversedMetaPath.reverse()
        metaPath = partialMetaPath if repeatLastType else partialMetaPath[:-1] # Don't repeat the middle entry
        modifiedMetaPath = metaPath + reversedMetaPath

        return modifiedMetaPath


    def __findLoopMetaPaths(self, graph, startingNode, metaPath, symmetric):
        """
          Helper function to find meta paths, given that we know the start and end nodes are the same
        """

        # Find reachable nodes on this shorter meta path
        reachableNodes, paths = self._findMetaPathsHelper(graph, startingNode, metaPath[1:-1], [], symmetric)

        returnPaths = []
        pathsFound = set()

        for path in paths:

            # Sanity check
            if startingNode.__class__ != metaPath[-1]:
                continue

            endingNode = path[-1]
            if not graph.hasEdge(endingNode, startingNode):
                continue
            if symmetric and not graph.hasEdge(startingNode, endingNode):
                continue

            thisPath = list(path) + [startingNode]

            # Check to see if we've already recorded this path
            if tuple(thisPath) in pathsFound:
                continue

            pathsFound.add(tuple(thisPath))
            returnPaths.append(thisPath)

        return returnPaths


    def __findNonLoopMetaPaths(self, graph, startingNode, endingNode, metaPath, symmetric):
        """
          Helper function to find meta paths, given that we know the start and end nodes are not the same
        """

        (metaPathNeighbors, paths) = self._findMetaPathsHelper(graph, startingNode, metaPath[1:], [], symmetric)
        return [list(path) for path in paths if path[-1] is endingNode]


    def _readFromCache(self, graph, node, metaPathTypes, symmetric):

        # If this graph was not loaded through an experiment (where a graph does not change dynamically), do not cache!
        if not hasattr(graph, 'inputPath'):
            return None

        strCacheKey = str((graph.inputPath, node.dictionary, [t.__name__ for t in metaPathTypes], symmetric))
        cacheKey = hashlib.sha256(strCacheKey).hexdigest()

        # Traditional cache miss case
        if not os.path.exists(os.path.join('cache', cacheKey)):
            return None

        # Load serialized data from cache & locate graph objects
        cacheData = cPickle.load(open(os.path.join('cache', cacheKey)))
        metaPathNeighbors = set(graph.dataMap[str(neighbor)] for neighbor in cacheData['metaPathNeighbors'])
        paths = set(tuple(graph.dataMap[str(d)] for d in path) for path in cacheData['paths'])

        return metaPathNeighbors, paths


    def _addToCache(self, graph, node, metaPathTypes, symmetric, metaPathNeighbors, paths):

        # If this graph was not loaded through an experiment (where a graph does not change dynamically), do not cache!
        if not hasattr(graph, 'inputPath'):
            return None

        strCacheKey = str((graph.inputPath, node.dictionary, [t.__name__ for t in metaPathTypes], symmetric))
        cacheKey = hashlib.sha256(strCacheKey).hexdigest()
        cacheData = {
            'metaPathNeighbors': [n.toDict() for n in metaPathNeighbors],
            'paths': [[node.toDict() for node in t] for t in paths]
        }

        cPickle.dump(cacheData, open(os.path.join('cache', cacheKey), 'w'))