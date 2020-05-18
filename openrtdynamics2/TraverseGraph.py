from .Signal import *
from .Block import *

from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)

class Node:
    def __init__(self, block : Block):
        self.block = block

    # return a list of linked nodes
    def getLinks(self):  
        pass


            




class TraverseGraph:
    # TODO: rename to TraverseBlocks

    # NOTE: THis is currently not needed but might be userd in the future for sth...

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

        # print(tabs + "....... depth " + str( depthCounter )  )

        #
        if startBlock.graphTraversionMarkerMarkIsVisited():
            print(tabs + "*** visited *** "  + startBlock.name + " (" + str( startBlock.id ) + ") ****")  ## TODO investigtare: why is this never reached?
            return

        # store this block as it is reachable
        self.reachableBlocks.append( startBlock )

        # make the node as visited
        startBlock.graphTraversionMarkerMarkVisited()

        print(tabs + "-- " + startBlock.name + " (" + str( startBlock.id ) + ") --" )



        # find out the links to other blocks
        for signal in startBlock.getOutputSignals():
            # for each output signal

            print(tabs + "-> S " + signal.name )

            if len( signal.getDestinationBlocks() ) == 0:
                print(tabs + '-- none --')

            for destinationBlock in signal.getDestinationBlocks():
                # destinationBlock is a link to a connected block

                print( tabs + "*", destinationBlock.name, "(", destinationBlock.id, ")"  )

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
            print(tabs + "*** visited *** "  + startBlock.name + " (" + str( startBlock.id ) + ") ****")  ## TODO investigtare: why is this never reached?
            return

        # check of the block 'startBlock'
        #if returnDependingInputs( signal )

        # store this block as it is reachable
        self.reachableBlocks.append( startBlock )

        # make the node as visited
        startBlock.graphTraversionMarkerMarkVisited()

        print(tabs + "--- " + startBlock.name + " (" + str( startBlock.id ) + ") --" )



        # find out the links to other blocks
        for signal in startBlock.getInputSignals():
            # for each output signal


            print(tabs + "-> S " + signal.name )

            if signal.getSourceBlock() is None:
                print(tabs + '-- ERROR: no input signal defined for this block! --')
                
            else:

                print( tabs + "*", signal.getSourceBlock().name, "(", signal.getSourceBlock().id, ")"  )

                self.forwardTraverse__( signal.getSourceBlock(), depthCounter = depthCounter + 1 )








class ExecutionLine():
    """
        contains a list 'signalOrder' of signals to be computed in the given order.
        The computation of these signals depends on a list of signals given by
        'dependencySignals'.
    """

    def __init__(self, signalOrder : List[ Signal ] , dependencySignals : List[ Signal ], dependencySignalsSimulationInputs : List[ Signal ], blocksToUpdateStates : List[ Block ], dependencySignalsThroughStates : List[ Signal ] ):
        self.signalOrder = signalOrder
        # self.dependencySignals = dependencySignals
        self.dependencySignalsSimulationInputs = dependencySignalsSimulationInputs
        self.blocksToUpdateStates = blocksToUpdateStates
        self.dependencySignalsThroughStates = dependencySignalsThroughStates

    def printExecutionLine(self):
        print("------ print of execution line -----")

        print(Fore.RED + "dependent sources:")

        # for s in self.dependencySignals:
        #     print("  - " + s.name )

        print(Fore.RED + "dependent sources (simulation inputs):")
                
        for s in self.dependencySignalsSimulationInputs:
            print("  - " + s.name )

        print(Fore.RED + "dependent sources (through state-dependend blocks):")
        
        for s in self.dependencySignalsThroughStates:
            print("  - " + s.name )

        print(Fore.GREEN + "execution order:")

        for s in self.signalOrder:
            print("  - " + s.name )

        print(Fore.GREEN + "blocks whose states must be updated:")

        for block in self.blocksToUpdateStates:
            print("  - " + block.name )


    def getSignalsToExecute(self):
        l = []

        #l.extend( self.dependencySignals )
        l.extend( self.signalOrder )

        return l


    def appendExecutionLine(self, executionLineToAppend):

        # merge dependencySignals: only add the elements of executionLineToAppend.dependencySignals
        # to self.dependencySignals that are not part of self.dependencySignals or self.signalOrder

        # TODO: use sets to merge..

        # for s in executionLineToAppend.dependencySignals:
        #     if not s in self.dependencySignals and not s in self.signalOrder:
        #         self.dependencySignals.append(s)


        for s in executionLineToAppend.dependencySignalsSimulationInputs:
            if not s in self.dependencySignalsSimulationInputs and not s in self.signalOrder:
                self.dependencySignalsSimulationInputs.append(s)

        
        for s in executionLineToAppend.dependencySignalsThroughStates:
            if not s in self.dependencySignalsThroughStates and not s in self.signalOrder:
                self.dependencySignalsThroughStates.append(s)

        


        original_list_tmp = self.signalOrder.copy()

        for s in executionLineToAppend.signalOrder:
            # TODO: (for optimization purposes) 
            # check if there comcon blocks in the list. (only in case a block has more than one
            # output signals and one of these signals is in the list executionLineToAppend.signalOrder
            # and another one in self.signalOrder  )

            # just append the 
            if not s in original_list_tmp:
                self.signalOrder.append( s )

            else:
                print("appendExecutionLine: skipped to add " + s.name)




        original_list_tmp = self.blocksToUpdateStates.copy()

        for b in executionLineToAppend.blocksToUpdateStates:
            # TODO: (for optimization purposes) 
            # check if there comcon blocks in the list. 

            # just append the 
            if not b in original_list_tmp:
                self.blocksToUpdateStates.append( b )





# NOTE: Simulation inputs might come twiche!




class BuildExecutionPath:
    """
        Find out the order in which signals have to be computed such that a given signal
        'signalToCalculte'can be calculated. This means finding out all dependencies of
        'signalToCalculte'. For each callc to 'getExecutionLine' only the signals that
        were not already marked as a dependeny in previous calls are returned.
        Each call to 'getExecutionLine' gives an instance 'ExecutionLine'
    """
    def __init__(self): #blockList : List[ Block ]

        # list of signals the computation depends on (the tips of the execution tree)
        self.dependencySignals = []

        self.dependencySignalsThroughStates = []

        # the list of signals to compute in correct order 
        self.execution_order = []
        # self.execution_order_without_targets = []

        # For each signgal self.execution_order there might be a blocks that
        # has an internal memory. It is required to build a list of those blocks
        # that need a state update after their output(s) are calculated.
        self.blocksToUpdateStates = []

        # list of marked signals (important to reset their visited flags)
        self.markedSignals = []

        # number of calls to getExecutionLine()
        self.level = 0

    def __del__(self):
        self.resetMarkers()


    def getExecutionLine(self, signalToCalculte : Signal):

        """
            get the order of computation steps and their order that have
            to be performed to compute 'signalToCalculte'
            
            For each call to this function, a list is generated that does not contain
            signals that are already part of a previous list (that are already computed)
            
            This function can be called multiple times and returns only the necessaray 
            computations. Computations already planned in previous calls of this function
            are not listed again. (until resetMarkers() is called)

            -- results --

            self.execution_order contains the list of signals to comute in the correct order including
            the target signals. Not included in this list are signals that cross the border to the simulation
            specified by signalToCalculte.system (coming from an outer system). Further, not included are
            signals that have been computet in a previous call to getExecutionLine().

            self.dependencySignals contains all signals that are required to comput signalToCalculate
            and either cross the border of a simulation, 
        """

        # TODO: dependency signals should stay as theiy are but reachableSignals should not contain signals
        #       that already have been calculated. Further, reachableSignals shall also contain dependency if they 
        #       were not already calculated

        print("getExecutionLine on level " + str(self.level) )

        # reset the lists
        self.execution_order = []
        self.dependencySignals = []
        self.dependencySignalsThroughStates = []
        self.dependencySignalsSimulationInputs = []
        self.blocksToUpdateStates = []

        # search within this system
        self.system = signalToCalculte.sim

        # compute by traversing the tree
        self.backwardTraverseSignalsExec__(startSignal=signalToCalculte, depthCounter = 0)

        # the iteration level
        self.level = self.level + 1

        return ExecutionLine( self.execution_order, self.dependencySignals, self.dependencySignalsSimulationInputs, self.blocksToUpdateStates, self.dependencySignalsThroughStates )

    def printExecutionLine(self):
        pass

    def resetMarkers(self):
        # reset graph traversion markers
        for signal in self.markedSignals:
            signal.graphTraversionMarkerReset()

        # reset status variables
        self.markedSignals = []
        self.level = 0

    def place_marker_for_current_level(self, signal):
        # mark the node/signal as being visited (meaning computed)
        signal.graphTraversionMarkerMarkVisited(self.level)
        self.markedSignals.append(signal)

    def isSignalAlreadyComputable(self, signal : Signal):
        return signal.graphTraversionMarkerMarkIsVisited()

    # Start backward traversion starting from the given startSignal
    def backwardTraverseSignalsExec__(self, startSignal : Signal, depthCounter : int, system_context = None):
        
        tabs = ''
        for i in range(0, depthCounter):
            tabs += '.  '


        if not (isinstance(startSignal, SimulationInputSignal) or isinstance(startSignal, BlockOutputSignal)):
            
            # this case must be an error..                  
            raise BaseException('not implemented or internal error: unexpected type of signal ' + startSignal.name)



        if startSignal.graphTraversionMarkerMarkIsVisitedOnLevelLowerThan(self.level):
            # - a previously computed signal has been reached

            print(Style.DIM + tabs + "has already been calculated in a previous traversion") 
            self.dependencySignals.append( startSignal )

            return

        if startSignal.graphTraversionMarkerMarkIsVisited():

            print(Style.DIM + tabs + "has already been calculated in this traversion") 
            return



        # check if the signal is a system input signal
        # is_simulation_input           = isinstance(startSignal, SimulationInputSignal)
        is_crossing_simulation_border = startSignal.is_crossing_system_boundary(self.system) #  self.system != startSignal.sim

        if is_crossing_simulation_border:
            # signal is an input to the simulation
            # add to the list of dependent inputs

            print(Fore.YELLOW + tabs + "  --> crosses system bounds")

            # startSignal is at the top of the tree, so add it to the dependiencies
            self.dependencySignals.append( startSignal )

            # also note down that this is a (actually used) simulation input
            self.dependencySignalsSimulationInputs.append( startSignal )

            print(Style.DIM + tabs + "added input dependency " + startSignal.toStr())

            # mark the node/signal as being visited (meaning computed)
            self.place_marker_for_current_level(startSignal)

            return


        # get the blocks prototype function to calculate startSignal
        block = startSignal.getSourceBlock()
        blocksPrototype = block.getBlockPrototype()

        #
        # check if the block that yields startSignal uses internal-states to compute startSignal
        #

        inputsToUpdateStatesTmp = blocksPrototype.returnInutsToUpdateStates( startSignal )
        if inputsToUpdateStatesTmp is not None:
            print(tabs + "--- signals needed *indirectly* for " + startSignal.name + " (through state update) --" )

            # 
            self.blocksToUpdateStates.append( block )

            # please note: blocksPrototype.returnInutsToUpdateStates might return some undetermined signals that are resolved here
            resolveUndeterminedSignals( inputsToUpdateStatesTmp )

            # add the signals that are required to perform the state update
            self.dependencySignalsThroughStates.extend( inputsToUpdateStatesTmp )

            for signal in inputsToUpdateStatesTmp:
                print(Fore.MAGENTA + tabs + "-> S " + signal.name )

            # mark the node/signal as being visited (meaning computed) ?????????????
            # self.place_marker_for_current_level(startSignal)

        #
        # find out the links to other signals but only these ones that are 
        # needed to calculate 'startSignal'
        #
        print(tabs + "--- signals needed for " + startSignal.name + " --" )

        dependingSignals = blocksPrototype.returnDependingInputs(startSignal)

        # please note: blocksPrototype.returnDependingInputs might return some undetermined signals that are resolved here
        resolveUndeterminedSignals( dependingSignals )

        if len(dependingSignals) == 0:
            # no dependencies to calculate startSignal (e.g. in case of const blocks or blocks without direct feedthrough)
            print(Style.DIM + tabs + "  (no signals needed) "  )

            # block startSignal.getSourceBlock() --> startSignal is a starting point

            # startSignal is at the top of the tree, so add it to the dependiencies
            self.dependencySignals.append( startSignal )

            #
            print(Style.DIM + tabs + "added " + startSignal.toStr())
            self.execution_order.append( startSignal )

            # mark the node/signal as being visited (meaning computed)
            self.place_marker_for_current_level(startSignal)

            return



        #
        # ITERATE: go through all signals needed to calculate startSignal
        #          only in case there are any, we come to this point
        #

        for signal in dependingSignals:

            print(Fore.MAGENTA + tabs + "-> S " + signal.name )

            self.backwardTraverseSignalsExec__( signal, depthCounter = depthCounter + 1 )

        #
        # FINALIZE: now also startSignal can be computed
        #

        #
        # store startSignal as reachable (put it on the exeution list)
        # NOTE: if startSignal is the tip of the tree (no dependingSignals) it is excluded
        #       from this list. However, it is still in the list of dependencySignals.
        #

        print(Style.DIM + tabs + "added " + startSignal.toStr())
        self.execution_order.append( startSignal )

        # mark the node/signal as being visited (meaning computed)
        self.place_marker_for_current_level(startSignal)
