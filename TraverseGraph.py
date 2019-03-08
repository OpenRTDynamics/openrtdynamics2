
from typing import Dict, List
from Signal import *
from Block import *


class Node:
    def __init__(self, block : Block ):
        self.block = block

    # return a list of linked nodes
    def getLinks(self):  
        pass






class TraverseGraph:
    def __init__(self): #blockList : List[ Block ]

        # # build a list of nodes
        # self.nodeList = []

        # for block in blockList:

        #     self.nodeList.append( Node(block) )

        # the list of reachable blocks
        self.reachableBlocks = []


    # Start forward traversion starting from the given startBlock
    def forwardTraverse(self, startBlock : Block):
        self.forwardTraverse__(startBlock)

        # reset graph traversion markers
        for block in self.reachableBlocks:
            block.graphTraversionMarkerReset()

    # Start forward traversion starting from the given startBlock
    def forwardTraverse__(self, startBlock : Block):
        #
        if startBlock.graphTraversionMarkerMarkIsVisited():
            print("Rached an already visited block")
            return

        # store this block as it is reachable
        self.reachableBlocks.append( startBlock )

        # make the node as visited
        startBlock.graphTraversionMarkerMarkVisited()

        print("traverse starting from ", startBlock.getBlockId() )

        # find out the links to other blocks
        for signal in startBlock.getOutputSignals():
            # for each output signal

            print("connected blocks to this signal:")

            for destinationBlock in signal.getDestinationBlocks():
                # destinationBlock is a link to a connected block


                print( destinationBlock.getBlockId() )

                # recursion
                self.forwardTraverse__( destinationBlock )




