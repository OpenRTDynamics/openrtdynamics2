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
    output_signals = system.primary_outputs

    # prepare (input filter of the given signals)
    resolveUndeterminedSignals(output_signals)

    # remove all anonymous signal
    system.resolve_anonymous_signals()



    #
    # compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
    # at runtime.
    #



    #
    # create execution path builder that manages the graph of the diagram and markings of the graph nodes.
    #

    dependency_graph_explorer=BuildExecutionPath(system)


    # append all execution lines to this structure
    executionLineToCalculateOutputs = ExecutionLine( [], [], [], [] )







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



    execution_line_to_compute_sink_blocks = ExecutionLine( [], [], sink_blocks_using_state_update, inputs_through_state_update_for_sinks )  # TODO! is this okay..? 

    # add
    executionLineToCalculateOutputs.appendExecutionLine( execution_line_to_compute_sink_blocks )








    #
    # look for output signals to be computed
    #

    signals_to_compute = set()
    signals_to_compute.update( set(output_signals) )
    signals_to_compute.update( set(system.signals_mandatory_to_compute) )

    for s in list(signals_to_compute):

        elForOutputS = dependency_graph_explorer.determine_execution_order( s, system, delay_level=0 )

        if enable_print > 1:
            elForOutputS.printExecutionLine()

        # merge all lines into one,
        # TODO use sets inside 'appendExecutionLine' some block are present twice
        executionLineToCalculateOutputs.appendExecutionLine( elForOutputS )











    # look into executionLineToCalculateOutputs.dependencySignals and use E.determine_execution_order( ) for each
    # element. Also collect the newly appearing dependency signals in a list and also 
    # call E.determine_execution_order( ) on them. Stop until no further dependend signal appears.
    # finally concatenare the execution lines

    # start with following signals to be computed
    simulationInputSignalsToCalculateOutputs = executionLineToCalculateOutputs.dependencySignalsSimulationInputs
    blocksToUpdateStates = executionLineToCalculateOutputs.blocksToUpdateStates
    dependencySignalsThroughStates = executionLineToCalculateOutputs.dependencySignalsThroughStates

    # counter for the delay level (i.e. step through all delays present in the system)
    delay_level = 1


    signalsToCache = []
    for s in executionLineToCalculateOutputs.signalOrder:

        if isinstance(s, UndeterminedSignal):
            raise BaseException("found anonymous signal during compilation")

        if isinstance(s, BlockOutputSignal) and not s.is_crossing_system_boundary(system):

            # only implement caching for intermediate computation results.
            # I.e. exclude the simulation input signals

            signalsToCache.append( s )


    # the simulation intputs needed to perform the state update
    # simulationInputSignalsToUpdateStates = set()

    # the list of blocks that are updated. Note: So far this list is only used to prevent
    # double updates.
    blocksWhoseStatesToUpdate_All = []

    # find out which signals must be further computed to allow a state-update of the blocks
    dependencySignals__ = dependencySignalsThroughStates + simulationInputSignalsToCalculateOutputs

    dependency_signals_through_states_that_are_already_computed = set()
    

    while True:

        if enable_print > 0:
            print("--------- Computing delay level "+ str(delay_level) + " --------")
        
        # backwards jump over the blocks that compute dependencySignals through their states.
        # The result is dependencySignals__ which are the inputs to these blocks
        if enable_print > 0:
            print(Style.DIM + "These sources are translated to (through their blocks via state-update):")

        # print the list of signals
        if enable_print > 0:
            print("-- dependencySignalsThroughStates signals __ --")
            for s in dependencySignalsThroughStates:
                print("  - " + s.name)

        # collect all executions lines build in this delay level in:
        executionLinesForCurrentOrder = []

        # iterate over all needed input signals and find out how to compute each signal
        for s in dependencySignalsThroughStates:

            # get execution line to calculate s
            executionLineForS = dependency_graph_explorer.determine_execution_order(s, system, delay_level=delay_level)

            # store this execution line
            executionLinesForCurrentOrder.append(executionLineForS)


        # merge all lines temporarily stored in 'executionLinesForCurrentOrder' into one 'executionLineForCurrentOrder'
        executionLineForCurrentOrder = ExecutionLine( [], [], [], [] )
        for e in executionLinesForCurrentOrder:

            # append execution line
            executionLineForCurrentOrder.appendExecutionLine( e )

        # update the list
        dependency_signals_through_states_that_are_already_computed.update( dependencySignalsThroughStates )


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
        #sUpCmd = CommandUpdateStates( blocksWhoseStatesToUpdate )
        #commandsToExecuteForStateUpdate.append( sUpCmd )

        # get the denpendent singals of the current delay level
        # TODO important: remove the signals that are already computable from this list
        #dependencySignals = executionLineForCurrentOrder.dependencySignals
        dependencySignalsSimulationInputs = executionLineForCurrentOrder.dependencySignalsSimulationInputs
        blocksToUpdateStates              = executionLineForCurrentOrder.blocksToUpdateStates
        dependencySignalsThroughStates    = executionLineForCurrentOrder.dependencySignalsThroughStates

        # find out which signals must be further computed to allow a state-update of the blocks
        dependencySignals__ = dependencySignalsThroughStates + dependencySignalsSimulationInputs

        # add the system inputs needed to update the states
        # simulationInputSignalsToUpdateStates.update( dependencySignalsSimulationInputs )

        # iterate
        delay_level = delay_level + 1
        if len(dependencySignals__) == 0:

            break

        if delay_level == 1000:
            raise BaseException(Fore.GREEN + "In system " +  system.name + ": the maximal number of iterations was reached. This is likely because of an algebraic loop.")
            break



    #
    computation_plan = dependency_graph_explorer.generate_computation_plan()



    # For each output generate a list of needed inputs
    o_input_signals = set() # input signals to compute the outputs
    o_clusters = []
    output_to_input_matrix = {}
    for s in output_signals:

        c = computation_plan.get_cluster_from_destination_signal( s )
        input_signals, _ = computation_plan.find_dependencies_of_cluster(c, reset_plan_builder = True)  

        o_input_signals.update( set( input_signals ) ) # .append( input_signals )
        o_clusters.append( c )

        output_to_input_matrix[ s ] = input_signals

    outputs_info = {
        'output_signals'          : output_signals,
        'input_signals'           : list(o_input_signals), # all input signals needed to compute all outputs
        'clusters'                : o_clusters,
        'output_to_input_matrix'  : output_to_input_matrix
    }

    # find blocks that need a state update
    blocks_that_need_a_state_update = list(dependency_graph_explorer.blocks_involved_in_a_state_update)
    signals_needed_for_state_update_of_involved_blocks = list(dependency_graph_explorer.signals_needed_for_state_update_of_involved_blocks)

    # collect clusters needed to perform the state update
    clusters_needed_for_state_update_of_involved_blocks = []
    for s in signals_needed_for_state_update_of_involved_blocks:

        c = computation_plan.get_cluster_from_destination_signal( s )

        if c is not None:
            clusters_needed_for_state_update_of_involved_blocks.append( c )

    
    
    input_signals, _ = computation_plan.find_dependencies_of_clusters(
        clusters_needed_for_state_update_of_involved_blocks,
        reset_plan_builder = True
    )  



    state_info = {
        'dependency_signals' : signals_needed_for_state_update_of_involved_blocks,
        'blocks'             : blocks_that_need_a_state_update,
        'clusters'           : clusters_needed_for_state_update_of_involved_blocks,
        'input_signals'      : list(input_signals) # [] # TODO: fill in
    }

    # build manifest
    manifest = SystemManifest( system.name, outputs_info, state_info )

    # use: blocksWhoseStatesToUpdate_All
    command_to_compute_clusters = CommandGenerateClusters(
        system,
        computation_plan,
        manifest,
        blocksWhoseStatesToUpdate_All
    )

    # simulationInputSignalsToUpdateStates is a set. Now fix the order of the signals to be consisten
    # simulation_input_signals_to_update_states_fixed_list = list(simulationInputSignalsToUpdateStates)

    # define the interfacing class
    command_to_execute_system = PutSystem(
        system = system,
        command_to_compute_clusters = command_to_compute_clusters
    )

    # collect all (needed) inputs to this system TODO: remove!
    #allinputs = set(( simulationInputSignalsToUpdateStates ))
    #allinputs.update( simulationInputSignalsToCalculateOutputs )
    #allinputs = list(allinputs)

    # collect the results
    compleResults = CompileResults( manifest, command_to_execute_system)

    compleResults.inputSignals                             = manifest.system_inputs  # allinputs
    compleResults.simulationInputSignalsToUpdateStates     = state_info['input_signals']  # simulation_input_signals_to_update_states_fixed_list
    compleResults.simulationInputSignalsToCalculateOutputs = outputs_info['input_signals'] # simulationInputSignalsToCalculateOutputs
    compleResults.outputSignals                            = output_signals


    # new!!!
    compleResults.outputs = outputs_info

    
    #
    return compleResults

