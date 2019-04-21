
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

        self.reachableSignals = []


    # Start forward traversion starting from the given startBlock
    def forwardTraverse(self, startBlock : Block):
        self.reachableBlocks = []

        # fill in self.reachableBlocks
        self.forwardTraverse__(startBlock, depthCounter = 0)

        # reset graph traversion markers
        for block in self.reachableBlocks:
            block.graphTraversionMarkerReset()

        return self.reachableBlocks

    # Start forward traversion starting from the given startBlock
    def forwardTraverse__(self, startBlock : Block, depthCounter : int):
        
        tabs = ''
        for i in range(0, depthCounter):
            tabs += '   '

        #print(tabs + "....... depth " + str( depthCounter )  )

        #
        if startBlock.graphTraversionMarkerMarkIsVisited():
            print(tabs + "*** visited *** "  + startBlock.getName() + " (" + str( startBlock.getBlockId() ) + ") ****")  ## TODO investigtare: why is this never reached?
            return

        # store this block as it is reachable
        self.reachableBlocks.append( startBlock )

        # make the node as visited
        startBlock.graphTraversionMarkerMarkVisited()

        print(tabs + "-- " + startBlock.getName() + " (" + str( startBlock.getBlockId() ) + ") --" )



        # find out the links to other blocks
        for signal in startBlock.getOutputSignals():
            # for each output signal

            print(tabs + "-> S " + signal.getName() )

            if len( signal.getDestinationBlocks() ) == 0:
                print(tabs + '-- none --')

            for destinationBlock in signal.getDestinationBlocks():
                # destinationBlock is a link to a connected block

                print( tabs + "*", destinationBlock.getName(), "(", destinationBlock.getBlockId(), ")"  )

            #for destinationBlock in signal.getDestinationBlocks():
                # destinationBlock is a link to a connected block

                # recursion
                self.forwardTraverse__( destinationBlock, depthCounter = depthCounter + 1 )






    # Start backward traversion starting from the given startBlock
    #
    # Note this is not fully tested 
    # DELETE SOON, if it is not needed
    #
    def backwardTraverseExec(self, startBlock : Block):
        self.reachableBlocks = []

        # fill in self.reachableBlocks
        self.backwardTraverseExec__(startBlock, depthCounter = 0)

        # reset graph traversion markers
        for block in self.reachableBlocks:
            block.graphTraversionMarkerReset()

        return self.reachableBlocks


    # Start backward traversion starting from the given startBlock
    def backwardTraverseExec__(self, startBlock : Block, depthCounter : int):
        
        tabs = ''
        for i in range(0, depthCounter):
            tabs += '   '

        #print(tabs + "....... depth " + str( depthCounter )  )

        #
        if startBlock.graphTraversionMarkerMarkIsVisited():
            print(tabs + "*** visited *** "  + startBlock.getName() + " (" + str( startBlock.getBlockId() ) + ") ****")  ## TODO investigtare: why is this never reached?
            return

        # check of the block 'startBlock'
        #if returnDependingInputs( signal )

        # store this block as it is reachable
        self.reachableBlocks.append( startBlock )

        # make the node as visited
        startBlock.graphTraversionMarkerMarkVisited()

        print(tabs + "--- " + startBlock.getName() + " (" + str( startBlock.getBlockId() ) + ") --" )



        # find out the links to other blocks
        for signal in startBlock.getInputSignals():
            # for each output signal


            print(tabs + "-> S " + signal.getName() )

            if signal.getSourceBlock() is None:
                print(tabs + '-- ERROR: no input signal defined for this block! --')
                

            else:

                # 


                print( tabs + "*", signal.getSourceBlock().getName(), "(", signal.getSourceBlock().getBlockId(), ")"  )

                self.forwardTraverse__( signal.getSourceBlock(), depthCounter = depthCounter + 1 )







    # Start backward traversion starting from the given startBlock
    def backwardTraverseSignalsExec(self, startSignal : Signal):
        self.reachableSignals = []

        # fill in self.reachableBlocks
        self.backwardTraverseSignalsExec__(startSignal, depthCounter = 0)

        # reset graph traversion markers
        for signal in self.reachableSignals:
            signal.graphTraversionMarkerReset()

        return self.reachableSignals


    # Start backward traversion starting from the given startSignal
    def backwardTraverseSignalsExec__(self, startSignal : Signal, depthCounter : int):
        
        tabs = ''
        for i in range(0, depthCounter):
            tabs += '   '

        #
        if startSignal.graphTraversionMarkerMarkIsVisited():
            print(tabs + "*** visited *** "  + startSignal.getName() + " (" + ") ****") 
            return

        # store this block as it is reachable
        self.reachableSignals.append( startSignal )

        # make the node as visited
        startSignal.graphTraversionMarkerMarkVisited()

        print(tabs + "--- " + startSignal.getName() + " (" + ") --" )

        # find out the links to other signals but only these ones that are 
        # needed to calculate 'startSignal'
        for signal in startSignal.getSourceBlock().getBlockPrototype().returnDependingInputs(startSignal):
            # for each input signal that is needed to compute 'startSignal'


            print(tabs + "-> S " + signal.getName() )

            if signal.getSourceBlock() is None:
                print(tabs + '-- ERROR: no input signal defined for this signal! --')
                
            else:

                self.backwardTraverseSignalsExec__( signal, depthCounter = depthCounter + 1 )

