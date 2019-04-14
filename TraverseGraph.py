
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
        self.forwardTraverse__(startBlock, depthCounter = 0)

        # reset graph traversion markers
        for block in self.reachableBlocks:
            block.graphTraversionMarkerReset()

        return self.reachableBlocks

    # Start forward traversion starting from the given startBlock
    def forwardTraverse__(self, startBlock : Block, depthCounter : int):
        
        tabs = ''
        for i in range(0, depthCounter):
            tabs += tabs + '  '

        print(tabs + "....... depth " + str( depthCounter )  )

        #
        if startBlock.graphTraversionMarkerMarkIsVisited():
            print(tabs + "**** Rached an already visited block: "  + startBlock.getName() + " (" + str( startBlock.getBlockId() ) + ") ****")  ## TODO investigtare: why is this never reached?
            return

        # store this block as it is reachable
        self.reachableBlocks.append( startBlock )

        # make the node as visited
        startBlock.graphTraversionMarkerMarkVisited()

        print(tabs + "traverse starting from " + startBlock.getName() + " (" + str( startBlock.getBlockId() ) + ")" )



        # find out the links to other blocks
        for signal in startBlock.getOutputSignals():
            # for each output signal

            print(tabs + "connected blocks to signal ", signal.getName() )

            if len( signal.getDestinationBlocks() ) == 0:
                print(tabs + '-- none --')

            for destinationBlock in signal.getDestinationBlocks():
                # destinationBlock is a link to a connected block


                print( tabs + "-", destinationBlock.getName(), "(", destinationBlock.getBlockId(), ")"  )

                # recursion
                self.forwardTraverse__( destinationBlock, depthCounter = depthCounter + 1 )




