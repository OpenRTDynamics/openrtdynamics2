from .system import *
#from .block_prototypes import *
from .graph_traversion import *
from .signal_network.signals import *
from .code_build_commands import *
from .system_manifest import *

from colorama import init,  Fore, Back, Style
init(autoreset=True)



class CompileResults(object):
    """
        compilation results for one system
        (excluding subsystems)
    """
    
    def __init__(self, manifest, command_to_execute):
        self._command_to_execute = command_to_execute
        self._manifest = manifest

    @property
    def manifest(self):
        return self._manifest

    @property
    def command_to_execute(self):
        return self._command_to_execute

    def set_command_to_execute(self, command_to_execute):
        self._command_to_execute = command_to_execute 



class CompileDiagram: # TODO: does this need to be a class? so far no.

    def __init__(self):

        # self._manifest = None
        self._comple_results = None

    @property
    def compileResults(self):
        return self._comple_results
    
    def traverseSubSystems(self, system : System, level, input_signals = None):

        is_top_level_system = system.upper_level_system is None

        # go deeper and compile subsystems first
        command_list_for_all_subsystems = []

        for subSystem in system.subsystems:
            compileResult = self.traverseSubSystems(subSystem, level=level+1)

            command_list_for_all_subsystems.append( compileResult.command_to_execute )

        # notify each block about the compilation of all subsystems in the system
        for block in system.blocks:
            block.blockPrototype.compile_callback_all_subsystems_compiled()

        #
        print("compiling system " + system.name + " (level " + str(level) + ")... " )

        # compile the system

        # TODO: when the inner system gets compiled, the system is okay (unmodified)
        #       as code generation is triggered, modified I/O signals are present which cases 
        #       the wrong block prototype to get called to produce the code (the ifsubsystem embedder is called)



        compile_result = compile_single_system(
            system, 
            reduce_not_needed_code = not is_top_level_system,
            subsytem_nesting_level = level,
            expected_system_inputs = input_signals
        )


        # # procedure commands for building/executing
        # command_list_for_all_subsystems = []
        # for subsystem in system.subsystems:
        #     command_list_for_all_subsystems.append( subsystem.command_to_execute )


        # replace the execution command by one that wraps all subsystems along with the main system
        execution_command = PutSystemAndSubsystems(
            command_to_put_main_system = compile_result.command_to_execute, 
            commands_to_put_subsystems = command_list_for_all_subsystems 
        )
        compile_result.set_command_to_execute( execution_command )

        # store the compilation result in the system's structure (TODO: is this needed?)
        system.compile_result = compile_result

        if is_top_level_system:
            self._comple_results = compile_result

        return compile_result



    def compile(self, system, input_signals = None):
        #
        # The datatypes of all signals must be determined here
        #

        if system.upper_level_system is not None:#
            # compilation can only start at top level subsystems
            raise BaseException("given system is not a top-level system (but instead a sub-system of sth.)")

        main_compile_result = self.traverseSubSystems(system, level = 0, input_signals = input_signals)

        if main_compile_result is None:
            raise BaseException("failed to compile system")

        self._comple_results = main_compile_result

        return main_compile_result



def compile_single_system(
    system, 
    reduce_not_needed_code = False, 
    enable_print:int=0, 
    subsytem_nesting_level : int = 0,    # 0 is the higher level system (the main system). 1 - is the first subsystem nesting level
    expected_system_inputs       = None  # the list of expected system inputs (optional)
):

    # the primary output signals are the outputs of the compiled system
    outputSignals = system.primary_outputs

    # prepare (input filter of the given signals)
    resolveUndeterminedSignals(outputSignals)

    # remove all anonymous signal
    system.resolve_anonymous_signals()



    #
    # compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
    # at runtime.
    #



    #
    # create execution path builder that manages the graph of the diagram and markings of the graph nodes.
    #

    E=BuildExecutionPath()

    # print("determining the computation order...")

    # append all execution lines to this structure
    executionLineToCalculateOutputs = ExecutionLine( [], [], [], [], [] )







    #
    # look for blocks mandatory to be computed (e.g., sink blocks)
    # and the required signals. NOTE: currently only sinks are supported
    # that are triggered on state update.
    #

    sink_blocks_using_state_update = []
    inputs_through_state_update_for_sinks = []

    for blk in system.blocks_in_system:
        if blk.output_signals is not None:
            if len(blk.output_signals) == 0: # no output signals --> must be a sink

                # print(Style.BRIGHT, "found a sink-type block in (sub)system", blk.name, system.name)

                inputs_to_update_states_tmp = blk.getBlockPrototype().config_request_define_state_update_input_dependencies( None )
                if inputs_to_update_states_tmp is not None:
                    # a sink that needs inputs for its state update
                    sink_blocks_using_state_update.append(blk)

                    # print("signals needed *indirectly* to compute sink (through state update)" )

                    # please note: blocksPrototype.config_request_define_state_update_input_dependencies might return some undetermined signals that are resolved here
                    resolveUndeterminedSignals( inputs_to_update_states_tmp )

                    # add the signals that are required to perform the state update
                    inputs_through_state_update_for_sinks.extend( inputs_to_update_states_tmp )

                    # for signal in inputsToUpdateStatesTmp:
                    #     print(Fore.MAGENTA + "-> S " + signal.name )



    execution_line_to_compute_sink_blocks = ExecutionLine( [], [], [], sink_blocks_using_state_update, inputs_through_state_update_for_sinks )

    # add
    executionLineToCalculateOutputs.appendExecutionLine( execution_line_to_compute_sink_blocks )








    #
    # look for output signals to be computed
    #

    signals_to_compute = set()
    signals_to_compute.update( set(outputSignals) )
    signals_to_compute.update( set(system.signals_mandatory_to_compute) )

    for s in list(signals_to_compute):

        elForOutputS = E.determine_execution_order( s, system )

        if enable_print > 1:
            elForOutputS.printExecutionLine()

        # merge all lines into one
        # TODO use sets inside 'appendExecutionLine' some block are present twice
        executionLineToCalculateOutputs.appendExecutionLine( elForOutputS )











    # print("building execution paths...")

    # look into executionLineToCalculateOutputs.dependencySignals and use E.determine_execution_order( ) for each
    # element. Also collect the newly appearing dependency signals in a list and also 
    # call E.determine_execution_order( ) on them. Stop until no further dependend signal appear.
    # finally concatenare the execution lines

    # start with following signals to be computed
    simulationInputSignalsToCalculateOutputs = executionLineToCalculateOutputs.dependencySignalsSimulationInputs
    blocksToUpdateStates = executionLineToCalculateOutputs.blocksToUpdateStates
    dependencySignalsThroughStates = executionLineToCalculateOutputs.dependencySignalsThroughStates

    # counter for the order (i.e. step through all delays present in the system)
    order = 0

    # execution line per order
    commandToCalcTheResultsToPublish = CommandCalculateOutputs(system, 
                                                                executionLineToCalculateOutputs, 
                                                                signals_to_compute,
                                                                no_memory_for_output_variables = True, 
                                                                output_signals=outputSignals )

    #
    # cache all signals that are calculated so far
    # TODO: make a one-liner e.g.  signalsToCache = removeInputSignals( executionLineToCalculateOutputs.signalOrder )
    #

    signalsToCache = []
    for s in executionLineToCalculateOutputs.signalOrder:

        if isinstance(s, UndeterminedSignal):
            raise BaseException("found anonymous signal during compilation")

        if isinstance(s, BlockOutputSignal) and not s.is_crossing_system_boundary(system):

            # only implement caching for intermediate computation results.
            # I.e. exclude the simulation input signals

            signalsToCache.append( s )

    commandToCacheIntermediateResults = CommandCacheOutputs( signalsToCache )

    # build the API function calcPrimaryResults() that calculates the outputs of the simulation.
    # Further, it stores intermediate results
    commandToPublishTheResults = PutAPIFunction(
        "calcResults_1", 
        inputSignals=simulationInputSignalsToCalculateOutputs,
        outputSignals=outputSignals, 
        executionCommands=[ commandToCalcTheResultsToPublish, commandToCacheIntermediateResults ],
        generate_wrappper_functions = not reduce_not_needed_code,
        subsystem_nesting_level  = subsytem_nesting_level
    )

    # Initialize the list of commands to execute to update the states
    commandsToExecuteForStateUpdate = []

    # restore the cache of output signals to update the states
    commandsToExecuteForStateUpdate.append( CommandRestoreCache(commandToCacheIntermediateResults) )

    # the simulation intputs needed to perform the state update
    simulationInputSignalsToUpdateStates = set()

    # the list of blocks that are updated. Note: So far this list is only used to prevent
    # double updates.
    blocksWhoseStatesToUpdate_All = []

    # find out which signals must be further computed to allow a state-update of the blocks
    dependencySignals__ = dependencySignalsThroughStates + simulationInputSignalsToCalculateOutputs

    dependency_signals_through_states_that_are_already_computed = set()
    

    while True:

        if enable_print > 0:
            print("--------- Computing order "+ str(order) + " --------")
        
        # backwards jump over the blocks that compute dependencySignals through their states.
        # The result is dependencySignals__ which are the inputs to these blocks
        if enable_print > 0:
            print(Style.DIM + "These sources are translated to (through their blocks via state-update):")

        # print the list of signals
        if enable_print > 0:
            print("-- dependencySignalsThroughStates signals __ --")
            for s in dependencySignalsThroughStates:
                print("  - " + s.name)

        # collect all executions lines build in this order in:
        executionLinesForCurrentOrder = []

        # iterate over all needed input signals and find out how to compute each signal
        for s in dependencySignalsThroughStates:

            # get execution line to calculate s
            executionLineForS = E.determine_execution_order(s, system)

            # store this execution line
            executionLinesForCurrentOrder.append(executionLineForS)


        # merge all lines temporarily stored in 'executionLinesForCurrentOrder' into one 'executionLineForCurrentOrder'
        executionLineForCurrentOrder = ExecutionLine( [], [], [], [], [] )
        for e in executionLinesForCurrentOrder:

            # append execution line
            executionLineForCurrentOrder.appendExecutionLine( e )

        # update the list
        dependency_signals_through_states_that_are_already_computed.update( dependencySignalsThroughStates )


        # create a command to calcurate executionLineForCurrentOrder and append to the
        # list of commands for state update: 'commandsToExecuteForStateUpdate'
        
        #
        # TODO (DONE): ensure somehow that variables are reserved for the inputs to the blocks
        #              whose states are updated
        #  executionLineForCurrentOrder.dependencySignalsSimulationInputs contains a list of input needed to update
        #  the states.
        #

        signals_from_system_states = signalsToCache

        commandsToExecuteForStateUpdate.append( CommandCalculateOutputs(system, 
                                                                        executionLineForCurrentOrder, 
                                                                        dependencySignals__, 
                                                                        signals_from_system_states=signals_from_system_states, 
                                                                        no_memory_for_output_variables = False) )

        #
        # find out which blocks need a call to update their states:
        # create commands for the blocks that have dependencySignals as outputs
        #

        if enable_print > 0:
            print("state update of blocks that yield the following output signals:")



        # TODO: rework this loop: use a set instead
        # blocksToUpdateStates Is already computed

        blocksWhoseStatesToUpdate = []

        for blk in blocksToUpdateStates:

            if not blk in blocksWhoseStatesToUpdate_All:
                # only add once (e.g. to prevent multiple state-updates in case two or more signals in 
                # dependencySignals are outputs of the same block)
                blocksWhoseStatesToUpdate.append( blk )
                blocksWhoseStatesToUpdate_All.append( blk )

                # added  blk.toStr
            else:
                #
                # already added blk.toStr()
                pass




        # create state update command and append to the list of commands to execute for state-update
        sUpCmd = CommandUpdateStates( blocksWhoseStatesToUpdate )
        commandsToExecuteForStateUpdate.append( sUpCmd )

        # get the denpendent singals of the current order
        # TODO important: remove the signals that are already computable from this list
        #dependencySignals = executionLineForCurrentOrder.dependencySignals
        dependencySignalsSimulationInputs = executionLineForCurrentOrder.dependencySignalsSimulationInputs
        blocksToUpdateStates              = executionLineForCurrentOrder.blocksToUpdateStates
        dependencySignalsThroughStates    = executionLineForCurrentOrder.dependencySignalsThroughStates


        # TODO: handle special case in which a simulation input is required for the state update of a block
        #       and was before found to be required to calculate the outpus of sth. 
        # instead of printing 'has already been calculated in a previous traversal' create an input to the update() function
        #
        # --- signals needed *indirectly* for s30 (through state update) --
        # -> S osc_excitement
        # -> S s22
        # --- signals needed for s30 --
        # -> S osc_excitement
        # .  has already been calculated in a previous traversal


        # find out which signals must be further computed to allow a state-update of the blocks
        dependencySignals__ = dependencySignalsThroughStates + dependencySignalsSimulationInputs

        # add the system inputs needed to update the states
        simulationInputSignalsToUpdateStates.update( dependencySignalsSimulationInputs )

        # iterate
        order = order + 1
        if len(dependencySignals__) == 0:
            # print(Fore.GREEN + "All dependencies are resolved.")

            break

        if order == 1000:
            raise BaseException(Fore.GREEN + "In system " +  system.name + ": the maximal number of iterations was reached. This is likely because of an algebraic loop.")
            break



    # simulationInputSignalsToUpdateStates is a set. Now fix the order of the signals to be consisten
    simulation_input_signals_to_update_states_fixed_list = list(simulationInputSignalsToUpdateStates)

    # Build API to update the states: e.g. c++ function updateStates()
    commandToUpdateStates = PutAPIFunction(
        nameAPI = 'updateStates', 
        inputSignals                = simulation_input_signals_to_update_states_fixed_list, 
        outputSignals               = [], 
        executionCommands           = commandsToExecuteForStateUpdate,
        generate_wrappper_functions = not reduce_not_needed_code,
        subsystem_nesting_level     = subsytem_nesting_level
    )

    # code to reset add blocks in the simulation
    commandsToExecuteForStateReset = CommandResetStates( blockList=blocksWhoseStatesToUpdate_All)

    # create an API-function resetStates()
    commandToResetStates = PutAPIFunction(
        nameAPI                     = 'resetStates', 
        inputSignals                = [], 
        outputSignals               = [], 
        executionCommands           = [commandsToExecuteForStateReset],
        generate_wrappper_functions = not reduce_not_needed_code,
        subsystem_nesting_level     = subsytem_nesting_level
    )


    # define the interfacing class
    command_to_execute_system = PutSystem(
        system = system,
        resetCommand = commandToResetStates, 
        updateCommand = commandToUpdateStates,
        outputCommand = commandToPublishTheResults
    )

    # collect all (needed) inputs to this system
    allinputs = set(( simulationInputSignalsToUpdateStates ))
    allinputs.update( simulationInputSignalsToCalculateOutputs )
    allinputs = list(allinputs)

    # build the manifest for the compiled system
    manifest = SystemManifest( command_to_execute_system, expected_system_inputs )

    compleResults = CompileResults( manifest, command_to_execute_system)

    compleResults.inputSignals                             = allinputs
    compleResults.simulationInputSignalsToUpdateStates     = simulation_input_signals_to_update_states_fixed_list
    compleResults.simulationInputSignalsToCalculateOutputs = simulationInputSignalsToCalculateOutputs
    compleResults.outputSignals                            = outputSignals

    
    #
    return compleResults

