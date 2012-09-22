import json
import os
import Stemmer
import cPickle
import networkx
from threading import Thread
from copy import deepcopy
from src.importer.error.ArnetParseError import ArnetParseError
from src.model.edge.dblp.Authorship import Authorship
from src.model.edge.dblp.Citation import Citation
from src.model.edge.dblp.Mention import Mention
from src.model.edge.dblp.Publication import Publication
from src.model.node.dblp.Author import Author
from src.model.node.dblp.Paper import Paper
from src.model.node.dblp.Topic import Topic
from src.model.node.dblp.Venue import Venue

__author__ = 'jon'


class ArnetMinerDataImporter(Thread):
    """
      Imports the DBLP citation data set (V5 format) into a python graph structure stored in NetworkX.
    """

    def __init__(self, inputPath, outputPath):

        self.inputPath = inputPath
        self.outputPath = outputPath

        projectRoot = os.environ['PROJECT_ROOT']

        # Get the stop words list / set
        self.stopWords = None
        with open(projectRoot + '/data/stopWords.json') as f:
            self.stopWords = set(json.load(f))

        self.stemmer = Stemmer.Stemmer('english')

        super(ArnetMinerDataImporter, self).__init__()


    def run(self):
        with open(self.inputPath) as inputFile:
            inputContent = inputFile.read()
        parsedData = self.parseInputContent(inputContent)
        graph = self.buildGraph(parsedData)

        with open(self.outputPath, 'w') as outputFile:
            cPickle.dump(outputFile, graph)


    def parseInputContent(self, inputContent):
        """
          Parses the input file content into basic data structures as an intermediate form before inserting into the graph.
        """

        arnetIdPrefix = '#arnetid'
        authorPrefix = '#@'
        citationPrefix = '#%'
        conferencePrefix = '#conf'
        indexPrefix = '#index'
        titlePrefix = '#*'
        yearPrefix = '#year'

        templatePaper = {
            'references': []
        }
        currentPaper = deepcopy(templatePaper)
        outputData = {}

        referencedPaperIds = set()
        paperIds = set()

        for inputLine in inputContent.split('\n'):
            inputLine = inputLine.strip()

            try:
                if inputLine.startswith(titlePrefix):
                    if currentPaper != templatePaper:
                        outputData[currentPaper['id']] = currentPaper
                        paperIds.add(currentPaper['id'])
                        currentPaper = deepcopy(templatePaper)
                    currentPaper['title'] = inputLine[len(titlePrefix):]
                elif inputLine.startswith(authorPrefix):
                    currentPaper['authors'] = inputLine[len(authorPrefix):].split(',')
                elif inputLine.startswith(yearPrefix):
                    currentPaper['year'] = int(inputLine[len(yearPrefix):])
                elif inputLine.startswith(conferencePrefix):
                    currentPaper['conference'] = inputLine[len(conferencePrefix):]
                elif inputLine.startswith(indexPrefix):
                    currentPaper['id'] = int(inputLine[len(indexPrefix):])
                elif inputLine.startswith(arnetIdPrefix):
                    currentPaper['arnetid'] = int(inputLine[len(arnetIdPrefix):])
                elif inputLine.startswith(citationPrefix):
                    referencedPaperId = int(inputLine[len(citationPrefix):])
                    referencedPaperIds.add(referencedPaperId)
                    currentPaper['references'].append(referencedPaperId)

                # Ignore other input lines

            except KeyError, error:
                raise ArnetParseError('Failed to parse data, missing paper attribute "%s"' % error.message)

        # Check that all citations are valid
        if referencedPaperIds.difference(paperIds) != set():
            raise ArnetParseError('Failed to parse data, invalid references in found')

        outputData[currentPaper['id']] = currentPaper

        return outputData


    def buildGraph(self, parsedData):
        """
          Form the DBLP graph structure from the parsed data
        """

        graph = networkx.DiGraph()

        # First, build the nodes for the graph
        authors = {} # Indexed by name
        papers = {} # Indexed by paper id
        topics = {} # Indexed by keyword
        venues = {} # Indexed by name
        citationMap = {} # Map of paper id to referenced paper ids

        # Construct everything except reference edges
        for paperId in parsedData:
            paperData = parsedData[paperId]

            paper = Paper(paperId, paperData['title'])
            citationMap[paperId] = paperData['references']

            # Create or get conference for this paper
            conferenceName = paperData['conference']
            if conferenceName not in venues:
                conference = Venue(len(venues), conferenceName)
                venues[conferenceName] = conference
                graph.add_node(conference)
            else:
                conference = venues[conferenceName]

            # Create or get authors for this paper
            paperAuthors = []
            for authorName in paperData['authors']:
                if authorName not in authors:
                    author = Author(len(authors), authorName)
                    authors[authorName] = author
                    graph.add_node(author)
                else:
                    author = authors[authorName]
                paperAuthors.append(author)

            # Extract keywords from title, and use as topics
            keywords = self.__extractKeywords(paperData['title'])
            for keyword in keywords:
                if keyword not in topics:
                    topic = Topic(len(topics), [keyword])
                    topics[keyword] = topic
                    graph.add_node(topic)
                else:
                    topic = topics[keyword]
                graph.add_edge(topic, paper, Mention().toDict())
                graph.add_edge(paper, topic, Mention().toDict())

            # Add new paper to the graph
            papers[paperId] = paper
            graph.add_node(paper)

            # Add corresponding edges in the graph
            for author in paperAuthors:
                graph.add_edge(paper, author, Authorship().toDict())
                graph.add_edge(author, paper, Authorship().toDict())
            graph.add_edge(paper, conference, Publication().toDict())
            graph.add_edge(conference, paper, Publication().toDict())

        # Add citations to the graph
        for paperId in citationMap:
            references = citationMap[paperId]
            paper = papers[paperId]
            for citedPaperId in references:
                citedPaper = papers[citedPaperId]
                graph.add_edge(paper, citedPaper, Citation().toDict())

        return graph


    def __extractKeywords(self, text):
        """
          Extracts topic keywords using lowercase, stemming, and a stop word list
        """

        keywords = set()
        words = self.stemmer.stemWords(text.lower().split(' '))
        for word in words:
            if word not in self.stopWords:
                keywords.add(word)

        return keywords
