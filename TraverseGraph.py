
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




class ExecutionLine():
    def __init__(self, signalOrder : List[ Signal ] , dependencySignals : List[ Signal ]):
        self.signalOrder = signalOrder
        self.dependencySignals = dependencySignals

    def printExecutionLine(self):
        print("------ print of execution line -----")

        print("dependent sources:")
        
        for s in self.dependencySignals:
            print("  - " + s.toStr() )

        print("execution order:")

        for s in self.signalOrder:
            print("  - " + s.toStr() )

    def appendExecutionLine(self, executionLineToAppend):

        # check if executionLineToAppend.dependencySignals are all in either self.signalOrder
        # or self.dependencySignals

        #for s in executionLineToAppend.dependencySignals:
        #    if not s in self.dependencySignals or not s in self.dependencySignals:
        #        raise BaseException("execution line cannot be appeded because the signal " + s.toStr() + " depends on signal not computed by the previous list")



        # merge dependencySignals: if only add the elements of executionLineToAppend.dependencySignals
        # to self.dependencySignals that are not part of self.dependencySignals or self.signalOrder

        for s in executionLineToAppend.dependencySignals:
            if not s in self.dependencySignals and not s in self.signalOrder:
                self.dependencySignals.append(s)
                # print("append " + s.toStr() + " to the list of dependencySignals")
            else:
                # print("did not append " + s.toStr() + " to the list of dependencySignals")
                pass

        for s in executionLineToAppend.signalOrder:
            # TODO: (for optimization purposes) 
            # check if there comcon blocks in the list. (only in case a block has more than one
            # output signals and one of these signals is in the list executionLineToAppend.signalOrder
            # and another one in self.signalOrder  )

            # just append the 
            self.signalOrder.append( s )







class BuildExecutionPath:
    def __init__(self): #blockList : List[ Block ]

        # list of signals the computation depends on (the tips of the execution tree)
        self.dependencySignals = []

        # the list of reachable signals
        self.reachableSignals = []

        # list of marked signals (important to reset their visited flags) (TODO implement)
        self.markedSignals = []

        # number of calls to getExecutionLine()
        self.level = 0

    def __del__(self):
        self.resetMarkers()


    def getExecutionLine(self, signalToCalculte : Signal):
        # get the order of computation steps and their order that have
        # to be performed to compute 'signalToCalculte'
        #
        # For each call to this function, a list is generated that does not contain
        # signals that are already part of a previous list (that are already computed)
        #
        # This function can be called multiple times and returns only the necessaray 
        # computations. Computations already planned in previous calls of this function
        # are not listed again. (until resetMarkers() is called)
        #   

        print("getExecutionLine on level " + str(self.level) )


        self.reachableSignals = []
        self.dependencySignals = []

        #self.backwardTraverseSignalsExec(signalToCalculte)
        self.backwardTraverseSignalsExec__(startSignal=signalToCalculte, startSignalPrevious = None, depthCounter = 0)

        # reverse of the list of reacheable signals gives the order of calculating the individual signals
        self.reachableSignals.reverse()

        #
        self.level = self.level + 1


        return ExecutionLine( self.reachableSignals, self.dependencySignals )


    def printExecutionLine(self):
        pass



    def resetMarkers(self):
        # reset graph traversion markers
        for signal in self.markedSignals:
            signal.graphTraversionMarkerReset()

        # reset status variables
        self.markedSignals = []
        self.level = 0


    # Start backward traversion starting from the given startSignal
    def backwardTraverseSignalsExec__(self, startSignal : Signal, startSignalPrevious : Signal, depthCounter : int):
        
        tabs = ''
        for i in range(0, depthCounter):
            tabs += '   '


        if startSignal.graphTraversionMarkerMarkIsVisitedOnLevel(self.level):
            # detected algeraic loop
            #
            # TODO: investigate if this is able to find all algebraic loops, i.e. also in case
            #       of multiple levels
            #
            print(tabs + "algebraic loop detected at signal " + startSignal.toStr())
            raise BaseException("algebraic loop detected at signal " + startSignal.toStr())


        #
        if startSignal.graphTraversionMarkerMarkIsVisited(self.level):
            # this could mean:
            # - an algebraic loop is present
            # - a previously computed signal has been reached

            print(tabs + "*** visited *** "  + startSignal.getName() + " (" + ") ****") 

            self.dependencySignals.append( startSignal )


            return

        # store this block as it is reachable
        print(tabs + "added " + startSignal.toStr())
        self.reachableSignals.append( startSignal )

        # mark the node visited
        startSignal.graphTraversionMarkerMarkVisited(self.level)
        self.markedSignals.append(startSignal)

        print(tabs + "--- " + startSignal.getName() + " (" + ") --" )

        # find out the links to other signals but only these ones that are 
        # needed to calculate 'startSignal'

        dependingSignals = startSignal.getSourceBlock().getBlockPrototype().returnDependingInputs(startSignal)

        if len(dependingSignals) == 0:
            # block startSignal.getSourceBlock() --> startSignal is a starting point

            self.dependencySignals.append( startSignal )

            pass
        else:


            for signal in dependingSignals:
                # for each input signal that is needed to compute 'startSignal'


                print(tabs + "-> S " + signal.getName() )

                if signal.getSourceBlock() is None:
                    print(tabs + '-- ERROR: no input signal defined for this signal! --')
                    
                else:

                    self.backwardTraverseSignalsExec__( signal, startSignalPrevious, depthCounter = depthCounter + 1 )

