from libdyn import *
from irpar import *
from BlockPrototypes import *
from TraverseGraph import *
from Signal import *
from ExecutionCommands import *
from CodeGenTemplates import *

from colorama import init,  Fore, Back, Style
init(autoreset=True)



class CompileResults(object):
    def __init__(self, manifest, commandToExecute):
        self._commandToExecute = commandToExecute
        self._manifest = manifest

    @property
    def manifest(self):
        return self._manifest

    @property
    def commandToExecute(self):
        return self._commandToExecute 



class CompileDiagram:

    def __init__(self):

        self._manifest = None


    # @property
    # def manifest(self):
    #     return self._manifest

    @property
    def compileResults(self):
        return self._compleResults

    def compile(self, sim, outputSignals):

        # prepare
        resolveUndeterminedSignals(outputSignals)

        #
        # compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
        # at runtime.
        #



        #
        # create execution path builder that manages the graph of the diagram and markings of the graph nodes.
        #

        E=BuildExecutionPath()


        print()
        print(Style.BRIGHT + "-------- Find dependencies for calcularing the outputs  --------")
        print()


        # collect all execution lines with:
        executionLineToCalculateOutputs = ExecutionLine( [], [], [], [] )

        # for all requested output singals
        for s in outputSignals:
            elForOutputS = E.getExecutionLine( s )
            elForOutputS.printExecutionLine()

            # merge all lines into one
            executionLineToCalculateOutputs.appendExecutionLine( elForOutputS )




        print()
        print(Style.BRIGHT + "-------- Build all execution paths  --------")
        print()

        # look into executionLineToCalculateOutputs.dependencySignals and use E.getExecutionLine( ) for each
        # element. Also collect the newly appearing dependency signals in a list and also 
        # call E.getExecutionLine( ) on them. Stop until no further dependend signal appear.
        # finally concatenare the execution lines

        # 

        # start with following signals to be computed
        dependencySignals = executionLineToCalculateOutputs.dependencySignals
        blocksToUpdateStates = executionLineToCalculateOutputs.blocksToUpdateStates

        # get the simulation-input signals in dependencySignals
        # NOTE: these are only the simulation inputs that are needed to calculate the output y
        simulationInputSignalsForCalcOutputs = []
        for s in dependencySignals:
            if isinstance(s, SimulationInputSignal):
                simulationInputSignalsForCalcOutputs.append(s)

        # counter for the order (i.e. step through all delays present in the system)
        order = 0


        # execution line per order
        commandToCalcTheResultsToPublish = CommandCalculateOutputs(executionLineToCalculateOutputs, outputSignals, defineVarsForOutputs = True)

        #
        # cache all signals that are calculated so far
        # TODO: make a one-liner e.g.  signalsToCache = removeInputSignals( executionLineToCalculateOutputs.signalOrder )
        #

        signalsToCache = []
        for s in executionLineToCalculateOutputs.signalOrder:

            if isinstance(s, UndeterminedSignal):
                raise BaseException("found anonymous signal during compilation")

            if isinstance(s, BlockOutputSignal):

                # only implement caching for intermediate computaion results.
                # I.e. exclude the simulation input signals

                signalsToCache.append( s )

        commandToCacheIntermediateResults = CommandCacheOutputs( signalsToCache )

        # build the API function calcPrimaryResults() that calculates the outputs of the simulation.
        # Further, it stores intermediate results
        commandToPublishTheResults = PutAPIFunction("calcResults_1", 
                                                    inputSignals=simulationInputSignalsForCalcOutputs,   # TODO: only add the elements that are inputs
                                                    outputSignals=outputSignals, 
                                                    executionCommands=[ commandToCalcTheResultsToPublish, commandToCacheIntermediateResults ] )

        # Initialize the list of commands to execute to update the states
        commandsToExecuteForStateUpdate = []

        # restore the cache of output signals to update the states
        commandsToExecuteForStateUpdate.append( CommandRestoreCache(commandToCacheIntermediateResults) )

        # the simulation intputs needed to perform the state update
        simulationInputSignalsForStateUpdate = []

        # the list of blocks that are updated. Note: So far this list is only used to prevent
        # double uodates.
        blocksWhoseStatesToUpdate_All = []

        while True:

            print("--------- Computing order "+ str(order) + " --------")
            print("dependent sources:")
                
            for s in dependencySignals:
                print(Fore.YELLOW + "  - " + s.toStr() )


            # collect all executions lines build in this order in:
            executionLinesForCurrentOrder = []

            # backwards jump over the blocks that compute dependencySignals through their states.
            # The result is dependencySignals__ which are the inputs to these blocks
            print(Style.DIM + "These sources are translated to (through their blocks via state-update):")

            dependencySignals__ = []
            for s in dependencySignals:

                # TODO: iterating over dependencySignals is not complete here: 
                # iterate over all signals that are connecteed to a block that 
                # has an internal state and an input that is needed to update 
                # the internal states

                # find out which signals are needed to calculate the states needed to calculate dependencySignals
                # returnInutsToUpdateStates

                if isinstance(s, SimulationInputSignal):
                    simulationInputSignalsForStateUpdate.append(s)

                elif isinstance(s, BlockOutputSignal):
                    # step over to (and iterate) the blocks inputs that are required for state-update
                    for s_ in s.getSourceBlock().getBlockPrototype().returnInutsToUpdateStates( s ):

                        print(Fore.YELLOW + Style.BRIGHT + "  - " + s_.toStr() )

                        # only append these signals is not already computable
                        if not E.isSignalAlreadyComputable(s_):
                            dependencySignals__.append(s_)

                        else:
                            print(Style.DIM + "    This signal is already computable (no futher execution line is calculated to this signal)")


            # iterate over all needed input signals and find out how to compute each signal
            for s in dependencySignals__:

                # get execution line to calculate s
                executionLineForS = E.getExecutionLine(s)

                #print('  - - - the line for signal - - - ' + s.toStr() )
                #executionLineForS.printExecutionLine()

                # store this execution line
                executionLinesForCurrentOrder.append(executionLineForS)


            # merge all lines temporarily stored in 'executionLinesForCurrentOrder' into one 'executionLineForCurrentOrder'
            executionLineForCurrentOrder = ExecutionLine( [], [], [], [] )
            for e in executionLinesForCurrentOrder:

                # append execution line
                executionLineForCurrentOrder.appendExecutionLine( e )

            #print('  - - - the line for this order - - - '  )
            #executionLineForCurrentOrder.printExecutionLine()


            # create a command to calcurate executionLineForCurrentOrder and append to the
            # list of commands for state update: 'commandsToExecuteForStateUpdate'
            
            #
            # TODO: ensure somehow that variables are reserved for the inputs to the blocks
            #       whose states are updated
            #

            commandsToExecuteForStateUpdate.append( CommandCalculateOutputs(executionLineForCurrentOrder, dependencySignals__, defineVarsForOutputs = False) )

            #
            # find out which blocks need a call to update their states:
            # create commands for the blocks that have dependencySignals as outputs
            #

            print("state update of blocks that yield the following output signals:")

            blocksWhoseStatesToUpdate = []
            for s in dependencySignals:
                # TODO: iterating over dependencySignals is not complete here: 
                # iterate over all signals that are connecteed to a block that 
                # has an internal state 


                print("  - " + s.getName())
                                
                if isinstance(s, BlockOutputSignal):
                    blk = s.getSourceBlock()

                    # NOTE: instead of checking if 'blk' is already in the list of blocks to update, the block could also be
                    # marked by a flag, which might be faster to execute.
                    if not blk in blocksWhoseStatesToUpdate_All:
                        # only add once (e.g. to prevent multiple state-updates in case two or more signals in 
                        # dependencySignals are outputs of the same block)
                        blocksWhoseStatesToUpdate.append( blk )
                        blocksWhoseStatesToUpdate_All.append( blk )

                        print("    (added) " + blk.toStr())
                    else:
                        print("    (already added) " + blk.toStr())

                if isinstance(s, SimulationInputSignal):
                    # append this signals s to the list of needed simulation inputs
                    # TODO: investigate if this is really needed and does not produce double appends to the list
                    # simulationInputSignalsForStateUpdate.append(s)

                    pass



            # create state update command and append to the list of commnds to execute for state-update
            sUpCmd = CommandUpdateStates( blocksWhoseStatesToUpdate )
            commandsToExecuteForStateUpdate.append( sUpCmd )

            #print("added command(s) to perform state update:")
            #sUpCmd.printExecution()

            # get the dependendy singals of the current order
            # TODO important: remove the signals that are already computable from this list
            dependencySignals = executionLineForCurrentOrder.dependencySignals
            blocksToUpdateStates = executionLineToCalculateOutputs.blocksToUpdateStates

            # iterate
            order = order + 1
            if len(dependencySignals) == 0:
                print(Fore.GREEN + "All dependencies are resolved")

                break

            if order == 1000:
                print(Fore.GREEN + "Maxmimum iteration limit reached -- this is likely a bug or your simulation is very complex")
                break




        # Build API to update the states: e.g. c++ function updateStates()
        commandToUpdateStates = PutAPIFunction( nameAPI = 'updateStates', 
                                                inputSignals=simulationInputSignalsForStateUpdate, 
                                                outputSignals=[], 
                                                executionCommands=commandsToExecuteForStateUpdate )

        # code to reset add blocks in the simulation
        commandsToExecuteForStateReset = CommandResetStates( blockList=sim.getBlocksArray() )

        # create an API-function resetStates()
        commandToResetStates = PutAPIFunction( nameAPI = 'resetStates', 
                                                inputSignals=[], 
                                                outputSignals=[], 
                                                executionCommands=[commandsToExecuteForStateReset] )


        # define the interfacing class
        commandToExecute_simulation = PutSimulation(    simulation = sim,
                                                        resetCommand = commandToResetStates, 
                                                        updateCommand = commandToUpdateStates,
                                                        outputCommand = commandToPublishTheResults
                                                    )

        # build the manifest for the compiled system
        manifest = SystemManifest( commandToExecute_simulation )

        self._compleResults = CompileResults( manifest, commandToExecute_simulation )

        #
        return self._compleResults

