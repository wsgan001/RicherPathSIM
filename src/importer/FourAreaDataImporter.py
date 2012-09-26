from Stemmer import Stemmer
import json
import logging
import os
import re
from threading import Thread
from src.importer.error.FourAreaParseError import FourAreaParseError
from src.logger.ColoredLogger import ColoredLogger
from src.graph.GraphFactory import GraphFactory
from src.model.node.dblp.Author import Author
from src.model.node.dblp.Conference import Conference
from src.model.node.dblp.Paper import Paper
from src.model.node.dblp.Topic import Topic

__author__ = 'jontedesco'

class FourAreaDataImporter(Thread):
    """
      Imports the simple data set from four research areas into the DBLP graph
    """

    def __init__(self, inputFolderPath, outputPath):

        self.inputFolderPath = inputFolderPath
        self.outputPath = outputPath

        logging.setLoggerClass(ColoredLogger)
        self.logger = logging.getLogger('FourAreaDataImporter')

        # Get the stop words set & stemmer for text analysis
        self.stopWords = None
        with open(os.getcwd() + '/src/importer/stopWords.json') as stopWordsFile:
            self.stopWords = set(json.load(stopWordsFile))
        self.stemmer = Stemmer('english')

        # Regex for stripping non-visible characters
        controlChars = ''.join(map(unichr, range(0,32) + range(127,160)))
        self.controlCharactersRegex = re.compile('[%s]' % re.escape(controlChars))

        super(FourAreaDataImporter, self).__init__()


    def run(self):

#        try:

            # Index of nodes by id
            nodeIndex = {}

            self.logger.info("Parsing ArnetMiner input node content")
            partialGraph, nodeIndex = self.parseNodeContent(nodeIndex)

#            self.logger.info("Parsing ArnetMiner input edge content")
#            graph = self.parseEdgeContent(partialGraph, nodeIndex)
#
#            self.logger.info("Pickling CoMoTo graph data to file")
#            with open(self.outputPath, 'w') as outputFile:
#                cPickle.dump(graph, outputFile)

#        except Exception, error:
#
#            self.logger.error(error.__class__.__name__ + ": " + error.message)


    def parseNodeContent(self, nodeIndex):
        """
          Parse the node content from the input files
        """

        graph = GraphFactory.createInstance()

        # Parse authors from file
        def authorLineParser(line):
            authorData = line.split()
            authorId = int(self.__removeControlCharacters(authorData[0]))
            authorName = ' '.join(authorData[1:])
            author = Author(authorId, authorName)
            return authorId, author
        self.__parseNodeType(authorLineParser, 'author', 'author.txt', graph, nodeIndex)


        # Parse conferences from file
        def conferenceLineParser(line):
            conferenceId, conferenceName = line.split()
            conferenceId = int(self.__removeControlCharacters(conferenceId))
            conference = Conference(conferenceId, conferenceName)
            return conferenceId, conference
        self.__parseNodeType(conferenceLineParser, 'conference', 'conf.txt', graph, nodeIndex)


        # Parse papers
        def paperLineParser(line):
            paperData = line.split()
            paperId = int(self.__removeControlCharacters(paperData[0]))
            paperTitle = ' '.join(paperData[1:])
            paper = Paper(paperId, paperTitle)
            return paperId, paper
        self.__parseNodeType(paperLineParser, 'paper', 'paper.txt', graph, nodeIndex)


        # Parse terms
        def termLineParser(line):
            topicId, term = line.split()
            topicId = int(self.__removeControlCharacters(topicId))
            # TODO: Use stemming & stop words list
            topic = Topic(topicId, [term])
            return topicId, topic
        self.__parseNodeType(termLineParser, 'topic', 'term.txt', graph, nodeIndex)

        return graph, nodeIndex


    def __parseNodeType(self, lineParser, typeName, fileName, graph, nodeIndex):
        """
          Parse the nodes for a particular node type, and add them to the graph & node index
        """

        nodeIndex[typeName] = {}

        inputFile = open(os.path.join(self.inputFolderPath, fileName))
        for line in inputFile:

            id, object = lineParser(line)

            if id in nodeIndex[typeName]:
                raise FourAreaParseError("Found duplicate node id %d parsing %ss" % (id, typeName))

            nodeIndex[typeName][id] = object
            graph.addNode(object)

        inputFile.close()


    def __removeControlCharacters(self, string):
        string = string.strip('\xef\xbb\xbf')
        return self.controlCharactersRegex.sub('', string)


if __name__ == '__main__':
    fourAreaDataImporter = FourAreaDataImporter('data/real/four_area', 'graphs/fourArea')
    fourAreaDataImporter.start()