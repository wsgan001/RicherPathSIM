from src.util.MetaPathUtility import MetaPathUtility

__author__ = 'jontedesco'

class DFSMetaPathUtility(MetaPathUtility):
    """
      Recursive implementation of meta path utility interface
    """

    def _findMetaPathsHelper(self, graph, node, metaPathTypes, previousNodes, symmetric):
        """
          Recursive helper function to recurse on nodes not yet visited according to types in meta path. This helper
          function cannot handle loops back to the original node, it assumes that we are only interested in paths that
          do not repeat any nodes, not even the start/end node.
        """

        # Prepare to use the cache if possible
        shouldCacheResults = len(previousNodes) == 0 and hasattr(graph, 'inputPath')

        # Pull from cache if possible
        try:
            cacheData = self._readFromCache(graph, node, metaPathTypes, symmetric)
            if shouldCacheResults and cacheData is not None:
                return cacheData
        except ValueError:
            print "Error reading from cache..."

        # Find the meta paths & meta path neighbors from this node
        metaPathNeighbors = set()
        paths = set()

        # Base case, we've reached the end of the meta path
        if len(metaPathTypes) == 0:
            return metaPathNeighbors, paths

        neighbors = graph.getSuccessors(node)
        for neighbor in neighbors:

            # Skip visited neighbors
            if neighbor in previousNodes:
                continue

            # Skip neighbors that don't match the next type in the meta path
            if neighbor.__class__ != metaPathTypes[0]:
                continue

            # If symmetry is enforced, skip neighbors that do not have both outgoing and incoming edges
            if symmetric and not (graph.hasEdge(neighbor, node) and graph.hasEdge(node, neighbor)):
                continue

            # If we're at the last node in the meta path, add it to the meta path neighbors
            if len(metaPathTypes) == 1:
                metaPathNeighbors.add(neighbor)
                paths.add(tuple(previousNodes + [node, neighbor]))
            else:

                # Otherwise, recurse & take union of all recursive calls
                neighborsFromThisNode, pathsFromThisNode = self._findMetaPathsHelper(
                    graph, neighbor, metaPathTypes[1:], previousNodes + [node], symmetric
                )
                paths = paths.union(pathsFromThisNode)
                metaPathNeighbors = metaPathNeighbors.union(neighborsFromThisNode)

        # Store in the cache if possible
        if shouldCacheResults:
            try:
                self._addToCache(graph, node, metaPathTypes, symmetric, metaPathNeighbors, paths)
            except UnicodeDecodeError:
                print "Skipping adding data to cache..."

        return metaPathNeighbors, paths

