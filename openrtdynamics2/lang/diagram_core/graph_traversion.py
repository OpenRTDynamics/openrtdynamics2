from .signal_network.signals import *
from .signal_network.Block import *
# from .system import * 


from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)



#
# NOTE: this is not used 
#
class graph_traversion2:

    def __init__(self):

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
        #if config_request_define_feedforward_input_dependencies( signal )

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
        This is a data structure
        
        It contains a list 'signalOrder' of signals to be computed in the given order.
        The computation of these signals depends on a list of signals given by
        'dependencySignals'.
    """

    def __init__(
        self,
        signalOrder : List[ Signal ],
        dependencySignals : List[ Signal ],
        dependencySignalsSimulationInputs : List[ Signal ],
        blocksToUpdateStates : List[ Block ],
        dependencySignalsThroughStates : List[ Signal ]
    ):
        self.signalOrder                       = signalOrder
        self.dependencySignals                 = dependencySignals  # TODO: check if this is still needed.
        self.dependencySignalsSimulationInputs = dependencySignalsSimulationInputs
        self.blocksToUpdateStates              = blocksToUpdateStates
        self.dependencySignalsThroughStates    = dependencySignalsThroughStates

    def printExecutionLine(self):
        print("------ print of execution line -----")

        print(Fore.RED + "dependent sources of any kind:")

        for s in self.dependencySignals:
            print("  - " + s.name )

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

        l.extend( self.signalOrder )

        return l


    def appendExecutionLine(self, executionLineToAppend):

        # merge dependencySignals: only add the elements of executionLineToAppend.dependencySignals
        # to self.dependencySignals that are not part of self.dependencySignals or self.signalOrder

        # TODO: to optimize: use sets to merge

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
            # check if there common blocks in the list. (only in case a block has more than one
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







class BuildExecutionPath:
    """
        Find out the order in which signals have to be computed such that a given signal
        'signal_to_calculate' can be calculated. This means finding out all dependencies of
        'signal_to_calculate'. For each call to 'determine_execution_order' only the signals that
        were not already marked as a dependency in previous calls are returned.
        Each call to 'determine_execution_order' gives an instance 'ExecutionLine'
    """
    def __init__(self, show_print:int=0):

        self._show_print = show_print

        # list of marked signals (important to reset their visited flags)
        self.marked_signals = []

        # number of calls to determine_execution_order()
        self.level = 0

    def __del__(self):
        # reset the grap markers stored in the signals
        self.reset_markers()


    def determine_execution_order(self, signal_to_calculate : Signal, current_system):

        """
            get the order of computation steps and their order that have
            to be performed to compute 'signal_to_calculate'
            
            For each call to this function, a list is generated that does not contain
            signals that are already part of a previous list (that are already computed)
            
            This function can be called multiple times and returns only the necessary 
            computations. Computations already planned in previous calls of this function
            are not listed again. (until reset_markers() is called)

            -- results --

            execution_order contains the list of signals to comute in the correct order including
            the target signals. Not included in this list are signals that cross the border to the simulation
            specified by signal_to_calculate.system (coming from an outer system). Further, not included are
            signals that have been computet in a previous call to determine_execution_order().

            dependency_signals contains all signals that are required to comput signalToCalculate
            and either cross the border of a simulation, 
        """

        # TODO: dependency signals should stay as they are but reachableSignals should not contain signals
        #       that already have been calculated. Further, reachableSignals shall also contain dependency if they 
        #       were not already calculated

        if self._show_print > 0:
            print("determine_execution_order on level " + str(self.level) )

        # compute by traversing the tree
        execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states = self.backwards_traverse_signals_exec__(start_signal=signal_to_calculate, depth_counter = 0, current_system=current_system)

        # the iteration level
        self.level = self.level + 1

        return ExecutionLine( execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states )

    def printExecutionLine(self):
        pass

    def reset_markers(self):
        # reset graph traversion markers
        for signal in self.marked_signals:
            signal.graphTraversionMarkerReset()

        # reset status variables
        self.marked_signals = []
        self.level = 0

    def place_marker_for_current_level(self, signal):
        # mark the node/signal as being visited (meaning computed)
        signal.graphTraversionMarkerMarkVisited(self.level)
        self.marked_signals.append(signal)

    # NOTE: unused
    def is_signal_already_computable(self, signal : Signal):
        return signal.graphTraversionMarkerMarkIsVisited()

    # Start backward traversion starting from the given startSignal
    def backwards_traverse_signals_exec__(self, start_signal : Signal, depth_counter : int, current_system):
        # WARNING: This is a recursive function!

        # the list of signals to compute in correct order 
        execution_order = []

        # list of signals the computation depends on (the tips of the execution tree)
        dependency_signals = []

        # the list of simulation input signals required for the computation
        dependency_signals_simulation_inputs = []

        # For each signgal execution_order there might be a blocks that
        # has an internal memory. It is required to build a list of those blocks
        # that need a state update after their output(s) are calculated.
        blocks_to_update_states = []

        #
        dependency_signals_through_states = []




        #
        # check if the datatype of startSignal is defined
        #

        if start_signal.datatype is None:
            raise BaseException('Unknown datatype for signal ' + start_signal.name + ': no datatype has been specified or could be determined automatically.')


        #
        #
        #

        
        tabs = ''
        for i in range(0, depth_counter):
            tabs += '.  '


        if not (isinstance(start_signal, SimulationInputSignal) or isinstance(start_signal, BlockOutputSignal)):
            
            # this case must be an error..                  
            raise BaseException('not implemented or internal error: unexpected type of signal ' + start_signal.name)

        # check if the signal is a system input signal
        is_crossing_simulation_border = start_signal.is_crossing_system_boundary(current_system) #  self.system != startSignal.sim

        # TODO: IMPLEMENT: except when startSignal is a simulation input (in this case it is not computed)
        #  and not isinstance(startSignal, SimulationInputSignal)
        if start_signal.graphTraversionMarkerMarkIsVisitedOnLevelLowerThan(self.level):
            # - a previously computed signal has been reached

            if self._show_print > 1:
                print(Style.DIM + tabs + "has already been calculated in a previous traversion") 

            dependency_signals.append( start_signal )

            # in case startSignal is a simulation input, still add it to the list of simulation input dependencies
            # though it has already been computed
            if is_crossing_simulation_border:

                if self._show_print > 1:
                    print(Style.DIM + tabs + "as it is also a simulation input, adding it to the list of depended inputs")

                # also note down that this is a (actually used) simulation input
                dependency_signals_simulation_inputs.append( start_signal )

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states

        if start_signal.graphTraversionMarkerMarkIsVisited():

            if self._show_print > 1:
                print(Style.DIM + tabs + "has already been calculated in this traversion") 

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states

        if is_crossing_simulation_border:
            # signal is an input to the system
            # add to the list of dependent inputs

            if self._show_print > 1:
                print(Fore.YELLOW + tabs + "  --> crosses system bounds")

            # startSignal is at the top of the tree, so add it to the dependencies
            dependency_signals.append( start_signal )

            # also note down that this is a (actually used) simulation input
            dependency_signals_simulation_inputs.append( start_signal )

            if self._show_print > 1:
                print(Style.DIM + tabs + "added input dependency " + start_signal.toStr())

            # mark the node/signal as being visited (meaning computed)
            self.place_marker_for_current_level(start_signal)

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states


        # get the blocks prototype function to calculate startSignal
        block = start_signal.getSourceBlock()
        blocksPrototype = block.getBlockPrototype()

        #
        # check if the block that yields startSignal uses internal-states to compute startSignal
        #

        inputs_to_update_states_tmp = blocksPrototype.config_request_define_state_update_input_dependencies( start_signal )
        if inputs_to_update_states_tmp is not None:

            if self._show_print > 1:
                print(tabs + "--- signals needed *indirectly* to compute " + start_signal.name + " (through state update) --" )

            # 
            blocks_to_update_states.append( block )

            # please note: blocksPrototype.config_request_define_state_update_input_dependencies might return some undetermined signals that are resolved here
            resolveUndeterminedSignals( inputs_to_update_states_tmp )

            # add the signals that are required to perform the state update
            dependency_signals_through_states.extend( inputs_to_update_states_tmp )

            if self._show_print > 1:
                for signal in inputs_to_update_states_tmp:
                    print(Fore.MAGENTA + tabs + "-> S " + signal.name )


        #
        # find out the links to other signals but only these ones that are 
        # needed to calculate 'startSignal'
        #

        if self._show_print > 1:
            print(tabs + "--- signals needed for " + start_signal.name + " --" )

        dependingSignals = blocksPrototype.config_request_define_feedforward_input_dependencies(start_signal)

        # please note: blocksPrototype.config_request_define_feedforward_input_dependencies might return some undetermined signals that are resolved here
        resolveUndeterminedSignals( dependingSignals )

        if len(dependingSignals) == 0:
            # no dependencies to calculate startSignal (e.g. in case of const blocks or blocks without direct feedthrough)
            if self._show_print > 1:
                print(Style.DIM + tabs + "  (no signals needed) "  )

            # block startSignal.getSourceBlock() --> startSignal is a starting point

            # startSignal is at the top of the tree, so add it to the dependencies
            dependency_signals.append( start_signal )

            #
            if self._show_print > 1:
                print(Style.DIM + tabs + "added " + start_signal.toStr())
    
            execution_order.append( start_signal )

            # mark the node/signal as being visited (meaning computed)
            self.place_marker_for_current_level(start_signal)

            return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states



        #
        # ITERATE: go through all signals needed to calculate startSignal
        #          only in case there are any, we come to this point
        #

        for signal in dependingSignals:

            if self._show_print > 1:
                print(Fore.MAGENTA + tabs + "-> S " + signal.name )

            if depth_counter > 100:
                raise BaseException('maximal number of iterations reached in system ' + signal.system.name + 'signal ' + signal.name)

            # R E C U R S I O N
            A_execution_order, A_dependency_signals, A_dependency_signals_simulation_inputs, A_blocks_to_update_states, A_dependency_signals_through_states = self.backwards_traverse_signals_exec__( signal, depth_counter = depth_counter + 1, current_system=current_system )

            execution_order.extend(                      A_execution_order )
            dependency_signals.extend(                   A_dependency_signals )
            dependency_signals_simulation_inputs.extend( A_dependency_signals_simulation_inputs )
            blocks_to_update_states.extend(              A_blocks_to_update_states )
            dependency_signals_through_states.extend(    A_dependency_signals_through_states )


        #
        # FINALIZE: now also startSignal can be computed
        #

        #
        # store startSignal as reachable (put it on the execution list)
        # NOTE: if startSignal is the tip of the tree (no dependingSignals) it is excluded
        #       from this list. However, it is still in the list of dependencySignals.
        #

        if self._show_print > 1:
            print(Style.DIM + tabs + "added " + start_signal.toStr())

        execution_order.append( start_signal )

        # mark the node/signal as being visited (meaning computed)
        self.place_marker_for_current_level(start_signal)


        return execution_order, dependency_signals, dependency_signals_simulation_inputs, blocks_to_update_states, dependency_signals_through_states
