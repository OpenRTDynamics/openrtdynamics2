from .system import *
from .signal_network.signals import *
from .signal_network import *
from .graph_traversion import *
from . import  code_generation_helper as cgh

from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)

from textwrap import *
from string import Template


#
# Code generation helper functions
#


def codegen_call_to_API_function_with_strutures(API_function_command, input_struct_varname, output_struct_varname):
    """
        help in code generation: create a function call to an API function (e.g. for calculating outputs or
        updateting states). Input and output parameters are taken from strutures with the given names. 
    """
    arguments_string = cgh.build_function_arguments_for_signal_io_with_struct(
        input_signals = API_function_command.inputSignals, 
        output_signals = API_function_command.outputSignals, 
        input_struct_varname = input_struct_varname, 
        output_struct_varname = output_struct_varname
    )
    return cgh.call_function_with_argument_str(fn_name=API_function_command.API_name, arguments_str=arguments_string)





#
# The execution command prototype
#

class ExecutionCommand(object):
    def __init__(self):

        # the nesting level (by default 0)
        self.treeLevel_ = 0

        # list of subcommands (filled in by derived classes)
        self.executionCommands = []

        # the upper level execution command within the execution tree
        # None by default
        self.contextCommand = None

        # object to define the tracing infrastructure (e.g. printf)
        # in case of None, tracing is deactivated
        self._tracing_infrastructure = None

    @property
    def treeLevel(self):
        return self.treeLevel_

    # set the parent execution command
    def setContext(self, context ):
        self.contextCommand = context
        self.treeLevel_ = context.treeLevel + 1

    def set_tracing_infrastructure(self, tracing_infrastructure):

        if isinstance(self, PutSystem):
            print('enabled tracing for system ' + str( self.API_name ))

        self._tracing_infrastructure = tracing_infrastructure

        for cmd in self.executionCommands:
            cmd.set_tracing_infrastructure( tracing_infrastructure )

    def generate_code_init(self, language):
        # 
        raise BaseException('generate_code_init unimplemented')

    def generate_code_destruct(self, language):
        raise BaseException('generate_code_destruct unimplemented')

    def generate_code(self, language, flag):

        lines = ''

        return lines




#
# The execution commands
#


# rename to CommandCalculateSignalValues
class CommandGenerateClusters(ExecutionCommand):
    """

    """

    def __init__(self, system, execution_plan, outputs, state_info):
        ExecutionCommand.__init__(self)

        self._system                     = system
        self.clusters                    = execution_plan.clusters
        self.execution_plan              = execution_plan
        self.outputs                     = outputs
        self.state_info                  = state_info


        # outputs = {
        #     'output_signals'      : output_signals,
        #     'dependency_signals'  : o_dependencies,
        #     'clusters'            : o_clusters
        # }

    def print_execution(self):
        pass

    def generate_code_init(self, language):
        pass

    def generate_code_destruct(self, language):
        pass


    def _code_for_dependency_tree(self):
        """
            generate code for resolving dependencies in-between clusters and execute them in the proper order 
        """


        # generate switch
        case_labels = [ c.id for c in self.clusters ]
        action_list = [ '_cluster_' + str(c.id) + '();' for c in self.clusters ]

        code_switch = cgh.cpp_generate_select( 'current_cluster_id', case_labels, action_list )


        code = """
void compute_cluster( int cluster_id ) {

    // init
    int current_cluster_id = cluster_id;

    while (true) {

        // look for dependencies
        bool ready_to_compute = true;

        for (int i = _cluster_counter[current_cluster_id]; ++i; i < _n_dependencies[current_cluster_id] ) {

            int dep_id = _dependencies[current_cluster_id][i];

            if ( !_cluster_executed[ dep_id ] ) {

                // remember where we stepped at# remember where we stepped at
                _cluster_counter[ current_cluster_id ] = i;

                // step to cluster on which the current one depends on
                _step_back_cluster[ dep_id ] = current_cluster_id;
                current_cluster_id = dep_id;

                ready_to_compute = false;

                break;
            }
            
        }

        if (!ready_to_compute)
            continue;

        // cluster can be computed
""" + cgh.indent( code_switch, 2 ) + """

        // mark cluster as executed
        _cluster_executed[current_cluster_id] = true;

        //
        if (current_cluster_id == cluster_id)
            abort;

        // step back
        current_cluster_id = _step_back_cluster[current_cluster_id];
    }
}

        """

        return code


    def generate_code(self, language, flag):

        print('CommandGenerateClusters', flag)

        lines = ''

        if language == 'c++':

            if flag == 'variables':

                # variables that describe the state of cluster computation
                lines += '\n// variables to keep track of executed clusters\n'
                lines += 'const static int _NUMBER_OF_CLUSTERS = ' + str(len( self.clusters )) + ';\n'

                lines += 'bool _cluster_executed[_NUMBER_OF_CLUSTERS];\n'
                lines += 'int _cluster_counter[_NUMBER_OF_CLUSTERS];\n'
                lines += 'int _step_back_cluster[_NUMBER_OF_CLUSTERS];\n'
                lines += '\n'

                # dependencies among clusters
                lines += '// cluster dependencies\n'

                for c in self.clusters:
                    depending_clusters = c.depending_clusters
                    lines += 'const int _dep_' + str(c.id) + '[' + str( len(depending_clusters) ) + '] = {' + ', '.join( [ str(c.id) for c in depending_clusters] ) + '};\n'

                lines += '\n'
                lines += 'const int *_dependencies[_NUMBER_OF_CLUSTERS] = {' + ', '.join([ '_dep_' + str(c.id) for c in self.clusters ]) + '};\n'
                lines += 'const int _n_dependencies[_NUMBER_OF_CLUSTERS] = {' + ', '.join([ str(len(c.depending_clusters)) for c in self.clusters ]) + '};\n'
                lines += '\n'

                # target signals
                lines += '\n// target signals for each cluster\n'
                lines += cgh.define_structure( 
                    name    = 'ClusterTargetValues', 
                    signals = [ c.destination_signal for c in self.clusters ]
                )
                lines += 'ClusterTargetValues _cluster_target_values;\n'
                lines += '\n'

                lines += '// references / memory for I/O\n'
                lines += 'Inputs _inputs;\n'
                lines += 'Outputs _outputs;\n'
                lines += '\n'




            if flag == 'code':
                lines += '\n// calculating clusters\n'

                lines += 'void _reset_clusters() {\n'
                lines += '  for (int _i = 0; _i < _NUMBER_OF_CLUSTERS; ++_i) {\n'
                lines += '    _cluster_executed[_i] = false;\n'
                lines += '    _cluster_counter[_i] = 0;\n'
                lines += '  }\n'
                lines += '}\n'



                def cpp_define_function_from_signals(fn_name, input_signals, output_signals, code):

                    lines = cgh.cpp_define_generic_function(
                        fn_name, 
                        return_cpp_type_str = 'void',
                        arg_list_str = ', '.join( cgh.define_variable_list( output_signals, make_a_reference=True ) + cgh.define_variable_list( input_signals, make_a_reference=True )  ),
                        code = code
                    )

                    return lines


                action_list = []
                
                for cluster in self.clusters:
                    
                    code_for_cluster = ''

                    code_for_cluster += '// needed input signal(s): ' + ', '.join( [s.name for s in cluster.dependency_signals_simulation_inputs] ) + '\n'
                    code_for_cluster += '// needed signal(s) from other clusters: ' + ', '.join( [s.name for s in cluster.dependency_signals_that_are_junctions] )  + '\n'
                    code_for_cluster += '// the target signal is ' + cluster.destination_signal.name  + '\n'
                    code_for_cluster += '\n'

                    # get input variables
                    code_for_cluster += '// input variables\n'
                    for s in cluster.dependency_signals_simulation_inputs:
                        code_for_cluster += cgh.defineVariable(s, make_a_reference=True ) + ' = _inputs.' + s.name + ';\n'

                    code_for_cluster += '\n'

                    # get target values of other clusters
                    code_for_cluster += '// cluster target variables\n'
                    for c in cluster.depending_clusters:
                        s = c.destination_signal
                        code_for_cluster += cgh.defineVariable(s, make_a_reference=True ) + ' = _cluster_target_values.' + s.name + ';\n'

                    # get the reference to the target values of the cluster
                    s = cluster.destination_signal
                    code_for_cluster += cgh.defineVariable(s, make_a_reference=True ) + ' = _cluster_target_values.' + s.name + ';\n'
                    code_for_cluster += '\n'

                    # define temp variables
                    code_for_cluster += '// temporary variables\n'
                    for s in cluster.dependency_signals_that_are_sources:
                        code_for_cluster += cgh.define_variable_line( s )

                    #
                    for s in cluster.execution_line:
                        if s is not cluster.destination_signal:
                            code_for_cluster += cgh.define_variable_line( s )

                    # newline
                    code_for_cluster += '\n'

                    # build code for all sources (blocks that have no inputs)
                    for s in cluster.dependency_signals_that_are_sources:
                        block = s.getSourceBlock()
                        code_for_cluster += block.getBlockPrototype().generate_code_output_list('c++', [s] )

                    # build code for all other blocks in the execution line
                    #
                    # TODO: introduce variable prefix '_cluster_target_values.XXX'
                    #
                    for s in cluster.execution_line:
                        block = s.getSourceBlock()
                        code_for_cluster += block.getBlockPrototype().generate_code_output_list('c++', [s] )

                    # put code to mark the cluster as executed
                    code_for_cluster += '\n_cluster_executed[' + str( cluster.id ) + '] = true;\n'


                    lines += cpp_define_function_from_signals(
                        '_cluster_' + str(cluster.id),
                        [], # cluster.dependency_signals_simulation_inputs,
                        [], # [cluster.destination_signal],
                        code_for_cluster
                    )

                lines += self._code_for_dependency_tree()
                lines += '\n'

                #
                # generate output trigger function
                #

                self.output_signals = []

                for i, s in enumerate(self.outputs['output_signals']):

                    c = self.outputs['clusters'][i]

                    # mapping output signal to cluster that computes the variable: s -> c


                # int _output_signal_index_to_cluster_id[3] = { 0, 3, 4 };
                
                ilines = ''
                ilines += 'int _output_signal_index_to_cluster_id[' + str(len(self.outputs['output_signals'])) + '] = {' + ', '.join( [ str(c.id) for c in self.outputs['clusters'] ] ) + '};\n'
                ilines += 'compute_cluster( _output_signal_index_to_cluster_id[output_signal_index] );\n'

                lines += cgh.cpp_define_generic_function('compute_output', 'void', 'int output_signal_index', ilines)
                lines += '\n'

                #
                # generate reset function
                #

                ilines = ''

                for b in self.state_info['blocks']:
                    ilines += '// reset ' + b.name + '\n'
                    ilines += b.getBlockPrototype().generate_code_reset('c++')


                lines += cgh.cpp_define_generic_function('reset', 'void', '', ilines)
                lines += '\n'

                #
                # generate update function
                #

                ilines = ''



                # # get input variables
                # code_for_cluster += '// input variables\n'
                # for s in cluster.dependency_signals_simulation_inputs:
                #     code_for_cluster += cgh.defineVariable(s, make_a_reference=True ) + ' = _inputs.' + s.name + ';\n'

 
                # get input variables
                ilines += '// input variables    TODO: handle system inputs to update the states\n'
                for s in self.state_info['input_signals']:
                    ilines += cgh.defineVariable(s, make_a_reference=True ) + ' = _inputs.' + s.name + ';\n'

                lines += '\n'

                # get target values of other clusters
                ilines += '// cluster target variables\n'
                for c in self.state_info['clusters']:

                    s = c.destination_signal

                    ilines += 'compute_cluster (' + str(c.id) + ');\n'

                    ilines += cgh.defineVariable(s, make_a_reference=True ) + ' = _cluster_target_values.' + s.name + ';\n'

                lines += '\n'

                for b in self.state_info['blocks']:
                    ilines += '// update block ' + b.name + '\n'
                    ilines += b.getBlockPrototype().generate_code_update('c++')


                lines += cgh.cpp_define_generic_function('update', 'void', '', ilines)
                lines += '\n'














                pass

        return lines




# rename to CommandCalculateSignalValues
class CommandCalculateOutputs(ExecutionCommand):
    """
        execute an executionLine i.e. call the output-flags of all blocks given in executionLine
        in the correct order. This calculates the blocks outputs indicated by the signals given
        in executionLine.getSignalsToExecute()

        system - the system of which to calculate the outputs
        target_signals - the signals to evaluate
        output_signal - signals foreseen to be system outputs (e.g. for them no memory needs to be allocated)
    """

    def __init__(self, system, executionLine, targetSignals, signals_from_system_states = [], no_memory_for_output_variables : bool = False, output_signals = []):
        ExecutionCommand.__init__(self)

        self._system                          = system
        self.executionLine                    = executionLine
        self.targetSignals                    = targetSignals
        self._output_signals                  = output_signals
        self._signals_from_system_states      = signals_from_system_states
        self.define_variables_for_the_outputs = not no_memory_for_output_variables

    def print_execution(self):
        signalListStr = '['

        if self.targetSignals is not None:
            signalListStr += cgh.signal_list_to_names_string(self.targetSignals)

        signalListStr += ']'

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: follow output execution line to calculate " + signalListStr + " using:")

        self.executionLine.printExecutionLine()

    def generate_code_init(self, language):
        pass

    def generate_code_destruct(self, language):
        pass

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'localvar':

                # 
                signals_reduced_set = self.executionLine.getSignalsToExecute().copy()

                # remove the system-output signals if requested
                if not self.define_variables_for_the_outputs: # This is flipped by its name
                    for s in self.targetSignals:

                        # if s is output signal of system 
                        if s in self._output_signals:

                            # s is a system output: the code that generates the source to calculate s shall not reserve memory for s

                            signals_reduced_set.remove( s )

                            # notify the block prototype that the signal s will be a system output
                            # and, hence, no memory shall be allocated for s (because the memory is already
                            # available)
                            s.getSourceBlock().getBlockPrototype().generate_code_setOutputReference('c++', s)
                            
                            
                            


                # skip the input signals in this loop (as their variables are already defined by the function API)
                for s in signals_reduced_set:

                    # remove also the variables that are states (e.g. in case they are defined by CommandRestoreCache(self._signals_from_system_states)
                    if not s in self._signals_from_system_states:

                        if not s.is_crossing_system_boundary(self._system): # TODO: Why is this needed?
                            # only implement caching for intermediate computation results.
                            # I.e. exclude the simulation input signals

                            if not s.is_referencing_memory:
                                lines += cgh.define_variable_line( s )



            if flag == 'code':
                lines += '\n// calculating the block outputs in the following order ' + cgh.signal_list_to_names_string(self.executionLine.signalOrder ) + '\n'
                lines += '// that depend on ' + cgh.signal_list_to_names_string(self.executionLine.dependencySignalsSimulationInputs) + '\n'
                lines += '// dependencies that require a state update are ' + cgh.signal_list_to_names_string(self.executionLine.dependencySignalsThroughStates) + ' \n'
                lines += '\n'


                # build map block -> list of signals
                blocks_with_outputs_to_compute = {}

                for s in self.executionLine.getSignalsToExecute():
                    # if isinstance(s, BlockOutputSignal): # TODO: is this neccessary?
                    if not s.is_crossing_system_boundary(self._system):
                        # only implement caching for intermediate computaion results.
                        # I.e. exclude the simulation input signals

                        block = s.getSourceBlock()

                        if block not in blocks_with_outputs_to_compute:
                            blocks_with_outputs_to_compute[ block ] = [ s ]
                        else:
                            blocks_with_outputs_to_compute[ block ].append( s )


                # for each blocks that provides outputs that are needed to compute,
                # generate the code to calculate these outputs.
                for block in blocks_with_outputs_to_compute:
                    lines += block.getBlockPrototype().generate_code_output_list('c++', blocks_with_outputs_to_compute[ block ] )
                    
        return lines




class CommandResetStates(ExecutionCommand):
    """
        call reset flag of all blocks given to this command
    """

    def __init__(self, blockList):
        ExecutionCommand.__init__(self)

        self.blockList = blockList
        
    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: reset states of:")

        for block in self.blockList:
            print("  - " + block.toStr() )

        # self.executionLine.printExecutionLine()

    def generate_code_init(self, language):
        pass

    def generate_code_destruct(self, language):
        pass

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += ''
                for b in self.blockList:
                    lines += b.getBlockPrototype().generate_code_reset('c++')

        return lines








class CommandUpdateStates(ExecutionCommand):
    """
        call update states of all blocks given to this command
    """

    def __init__(self, blockList):
        ExecutionCommand.__init__(self)

        self.blockList = blockList
        
    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: update states of:")

        for block in self.blockList:
            print("  - " + block.toStr() )

        # self.executionLine.printExecutionLine()

    def generate_code_init(self, language):
        pass

    def generate_code_destruct(self, language):
        pass

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                # define all state variables

                lines += ''
                lines += "\n\n// state update\n"
                for b in self.blockList:
                    
                    #
                    # TODO: rename 'defStates' to 'variables'
                    #
                    
                    lines += b.getBlockPrototype().generate_code_defStates('c++')

            if flag == 'code':
                lines += '\n'
                lines += ''

                for b in self.blockList:
                    lines += b.getBlockPrototype().generate_code_update('c++')


        return lines







class CommandCacheOutputs(ExecutionCommand):
    """
        copy the value of each given signal to the space of global variables
        (only signals that are the output of a block are considered, i.e. no 
        simulation inputs)
    """

    def __init__(self, signals : List[Signal]):
        ExecutionCommand.__init__(self)

        self.signals = signals
        
    def get_cachedSignals(self):
        return self.signals

    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: cache the following outputs (so that they do not need to be recalculated):")

        for s in self.signals:
            print("  - " + s.toStr() )

    def generate_code_init(self, language):
        pass

    def generate_code_destruct(self, language):
        pass

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':


            if flag == 'variables':
                lines += ''
                lines += "\n\n//\n// cached output values\n//\n\n"
                for s in self.signals:

                    cachevarName = s.name + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()

                    if not s.is_referencing_memory:
                        # lines +=  '\n// cache for ' + s.name + '\n'
                        lines +=  s.getDatatype().cpp_define_variable(cachevarName) + ";" + '\n' 

                    else:
                        comment = ' // cache for ' + s.name + ' (stores a pointer to a memory location)'
                        lines +=  s.getDatatype().cpp_define_variable('(*' + cachevarName + ')') + ";" + comment + '\n' 


            if flag == 'code':
                lines += '\n'
                lines += '// saving the signals ' + cgh.signal_list_to_names_string(self.signals) + ' into the states \n'


                for s in self.signals:
                    cachevarName = s.name + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()

                    if not s.is_referencing_memory:
                        lines += cachevarName + ' = ' + s.name + ';\n'
                    else:
                        # get the raw-pointer for the reference
                        lines += cachevarName + ' = &(' + s.name + '); // just copy a pointer to the memory location\n'

        return lines






class CommandRestoreCache(ExecutionCommand):
    """
        restore the cached signals that were previously stored by the command 
        cacheCommand : CommandCacheOutputs
    """

    def __init__(self,  cacheCommand : CommandCacheOutputs ):
        ExecutionCommand.__init__(self)

        self.signals = cacheCommand.get_cachedSignals()
        
    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: read cache of the following outputs (so that they do not need to be recalculated):")

        for s in self.signals:
            print("  - " + s.toStr() )

    def generate_code_init(self, language):
        pass

    def generate_code_destruct(self, language):
        pass

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += '\n'
                lines += '// restoring the signals ' + cgh.signal_list_to_names_string(self.signals) + ' from the states \n'

                for s in self.signals:

                    cachevarName = s.name + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()

                    if not s.is_referencing_memory:
                        lines +=  s.getDatatype().cpp_define_variable( s.name, make_a_reference=True ) + ' = ' + cachevarName + ";" + '\n' 
                    else:
                        # set the reference to the memory the pointer 'cachevarName' is pointing to
                        lines +=  s.getDatatype().cpp_define_variable( s.name, make_a_reference=True ) + ' = *' + cachevarName + ";" + ' // use a pointer to the memory location\n' 


                lines += '\n'

        return lines






class PutAPIFunction(ExecutionCommand):
    """
        Represents an API-function (e.g. member function of a c++ class) which executes --
        once triggered -- the specified commands. A list of in-/output signals to this function
        is given by inputSignals and outputSignals.
    """

    #
    # Creates an API-function to return the calculated values that might depend on input values
    # 

    def __init__(
        self, 
        nameAPI : str, 
        inputSignals : List[ Signal ], 
        outputSignals : List[ Signal ], 
        executionCommands, 
        generate_wrappper_functions = True,
        subsystem_nesting_level : int = 0
    ):
        ExecutionCommand.__init__(self)

        self.outputSignals = outputSignals
        self.inputSignals = inputSignals
        self.executionCommands = executionCommands
        self._nameAPI = nameAPI
        self._generate_wrappper_functions = generate_wrappper_functions
        self._subsystem_nesting_level = subsystem_nesting_level

        # check if there are no common signal names in in/output
        for so in self.outputSignals:
            for si in self.inputSignals:
                if so.name == si.name:
                    raise BaseException('the systems in-/outputs have a common signal name: ' + si.name + '. This is not supported in code generation. Please use a different signal name for the output or the input.')

        for e in executionCommands:
            e.setContext(self)


    @property
    def API_name(self):
        return self._nameAPI
        
    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: API outputs are:")
        for s in self.outputSignals:
            print(Style.DIM + '  - ' + s.name)

        print(Style.BRIGHT + Fore.YELLOW + "that are calculated by: {")
        
        for c in self.executionCommands:
            c.print_execution()

        print(Style.BRIGHT + Fore.YELLOW + "}")
        
    def generate_code_init(self, language):
        for c in self.executionCommands:
            c.generate_code_init(language)

    def generate_code_destruct(self, language):
        for c in self.executionCommands:
            c.generate_code_destruct(language)

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                for c in self.executionCommands:
                    lines += c.generate_code(language, 'variables')


            if flag == 'code':
                #
                # ------ define the API-function ------
                #
                if len(self.outputSignals) > 0:
                    lines += '// API-function ' + self._nameAPI + ' to compute: ' + cgh.signal_list_to_names_string( self.outputSignals )
                else:
                    lines += '// API-function ' + self._nameAPI

                lines += '\n'

                # innerLines will be put into the functions
                function_code = ''

                # place tracing (begin)
                if self._tracing_infrastructure is not None:

                    space = cgh.tabs(self._subsystem_nesting_level)

                    function_code += cgh.create_printf(
                        intro_string = Fore.GREEN + space + 'ENTR: ' + Fore.YELLOW + self.contextCommand.API_name + Fore.RESET + '/' + Style.DIM + self._nameAPI + Style.RESET_ALL,
                        signals      = self.inputSignals
                    )

                    function_code += '\n'
                
                # put the local variables
                for c in self.executionCommands:
                    function_code += c.generate_code(language, 'localvar')
                
                function_code += '\n'

                # put the code
                for c in self.executionCommands:
                    function_code += c.generate_code(language, 'code')

                # place tracing (end)
                if self._tracing_infrastructure is not None:

                    space = cgh.tabs(self._subsystem_nesting_level)

                    function_code += cgh.create_printf(
                        intro_string = Fore.RED + space + 'EXIT: ' + Fore.YELLOW + self.contextCommand.API_name + Fore.RESET + '/' + Style.DIM + self._nameAPI + Style.RESET_ALL,
                        signals     = self.outputSignals
                    )

                    function_code += '\n'

                # generate the function
                lines += cgh.cpp_define_function(self._nameAPI, self.inputSignals, self.outputSignals, function_code )

                #
                # ------ end of 'define the API-function' ------
                #

                if self._generate_wrappper_functions:

                    # put data strutures to hold I/O signals
                    lines += '// output signals of  ' + self._nameAPI + '\n'
                    lines += cgh.define_structure('Outputs_' + self._nameAPI , self.outputSignals)  

                    lines += '// input signals of ' + self._nameAPI + '\n'
                    lines += cgh.define_structure('Inputs_' + self._nameAPI , self.inputSignals)  

                    #
                    # put a wrapper function that offers a 'nicer' API using structures for in- and output signals
                    #

                    function_code = ''
                    function_code += cgh.define_struct_var( 'Outputs_' + self._nameAPI, 'outputs'  ) + '\n'

                    # call to wrapped function
                    function_code += codegen_call_to_API_function_with_strutures(API_function_command=self, input_struct_varname='inputs', output_struct_varname='outputs')

                    function_code += '\n'
                    function_code += 'return outputs;\n'

                    #
                    lines += '// wrapper function for ' + self._nameAPI + '\n'
                    lines += cgh.cpp_define_generic_function( 
                        fn_name=self._nameAPI + '__', 
                        return_cpp_type_str = 'Outputs_' + self._nameAPI, 
                        arg_list_str = 'Inputs_' + self._nameAPI + ' inputs', 
                        code = function_code
                    )



        return lines




class PutSystem(ExecutionCommand):
    """
        Represents a system that is represented by a class in c++
    """

    def __init__(
        self, 
        system : System,
        resetCommand : PutAPIFunction,
        updateCommand : PutAPIFunction,
        outputCommand : PutAPIFunction,
        command_to_compute_clusters : PutAPIFunction,
    ):
        ExecutionCommand.__init__(self)
        self.executionCommands = [ resetCommand, updateCommand, outputCommand, command_to_compute_clusters ] 

        self.resetCommand = resetCommand
        self.updateCommand = updateCommand
        self.outputCommand = outputCommand
        self.command_to_compute_clusters = command_to_compute_clusters

        self._api_function_names = {'calculate_output' : self.outputCommand.API_name,
                         'state_update' : self.updateCommand.API_name,
                         'reset' : self.resetCommand.API_name }

        self._api_functions = {'calculate_output' : self.outputCommand,
                         'state_update' : self.updateCommand,
                         'reset' : self.resetCommand }


        self.system = system
        self.nameAPI = system.getName()

        for e in self.executionCommands:
            e.setContext(self)



    @property
    def API_name(self):
        return self.nameAPI

    @property
    def API_functionNames(self):
        return self._api_function_names
        
    @property
    def API_functions(self):
        return self._api_functions

    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: System with the API (" + self.nameAPI + "):")
        
        for c in self.executionCommands:
            c.print_execution()

        print(Style.BRIGHT + Fore.YELLOW + "}")
        
    def generate_code_init(self, language):

        for c in self.executionCommands:
            c.generate_code_init(language)

        # call init codegen for each block in the simulation
        for block in self.system.blocks:
            block.getBlockPrototype().generate_code_init(language)


    def generate_code_destruct(self, language):
        for c in self.executionCommands:
            c.generate_code_destruct(language)

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                pass

            if flag == 'code':
                #
        
                # Add code within the same namespace this simulation sits in.
                # E.g. to add helper functions, classes, ...
                for b in self.system.blocks:
                    lines += b.getBlockPrototype().codegen_addToNamespace(language)

                # define the API-function (start)
                lines += 'class ' + self.nameAPI + ' {'
                lines += '\n'

                inner_lines = ''

                #
                # define structures that combine all in- and outputs
                #

                config_pass_by_reference = True

                all_input_signals = list(set(self.resetCommand.inputSignals + self.updateCommand.inputSignals + self.outputCommand.inputSignals))
                all_output_signals = self.outputCommand.outputSignals

                # introduce a structure that combines all system inputs
                inner_lines += '// all system inputs and outputs combined\n'
                inner_lines += cgh.define_structure('Inputs', all_input_signals)
                inner_lines += cgh.define_structure('Outputs', all_output_signals)

                #
                # put the local variables
                #

                inner_lines += '// variables\n'
                inner_lines += 'public:\n'
                for c in self.executionCommands:
                    inner_lines += c.generate_code(language, 'variables')
                
                inner_lines += '\n'

                # put the code
                for c in self.executionCommands:
                    inner_lines += c.generate_code(language, 'code')



                #
                # define the generic step functions
                #

                function_code = ''
                if not config_pass_by_reference:
                    function_code += cgh.define_struct_var( 'Outputs', 'outputs'  ) + '\n'

                # call to reset function
                function_code_reset_states = codegen_call_to_API_function_with_strutures(API_function_command=self.resetCommand, input_struct_varname='inputs', output_struct_varname='outputs')

                # call to output function (1)
                function_code_calc_output = codegen_call_to_API_function_with_strutures(API_function_command=self.outputCommand, input_struct_varname='inputs', output_struct_varname='outputs')

                # call to update function
                function_code_update_states = codegen_call_to_API_function_with_strutures(API_function_command=self.updateCommand, input_struct_varname='inputs', output_struct_varname='outputs')

                # conditional update / output
                function_code += cgh.generate_if_else(language, condition_list=['reset_states'], action_list=[function_code_reset_states] )
                function_code += cgh.generate_if_else(language, condition_list=['calculate_outputs==1'], action_list=[function_code_calc_output] )
                function_code += cgh.generate_if_else(language, condition_list=['update_states'], action_list=[function_code_update_states] )



                function_code += '\n'

                if not config_pass_by_reference:
                    function_code += 'return outputs;\n'

                #
                if self.system.upper_level_system is None:
                    # put an interface function for nice interaction for the user of the generated code
                    # Do this only for the top-level system
                    
                    inner_lines += '// main step function \n'

                    if config_pass_by_reference:
                        inner_lines += cgh.cpp_define_generic_function( 
                            fn_name='step', 
                            return_cpp_type_str = 'void', 
                            arg_list_str = 'Outputs & outputs, Inputs const & inputs, int calculate_outputs, bool update_states, bool reset_states', 
                            code = function_code
                        )
                    else:
                        inner_lines += cgh.cpp_define_generic_function( 
                            fn_name='step', 
                            return_cpp_type_str = 'Outputs', 
                            arg_list_str = 'Inputs inputs, int calculate_outputs, bool update_states, bool reset_states', 
                            code = function_code
                        )




                # define the API-function (finish)
                lines += cgh.indent(inner_lines)
                lines += '};\n\n'

        return lines






class PutSystemAndSubsystems(ExecutionCommand):
    """
        Represents a system and its subsystem togethter that is represented by multiple classes in c++.
        Aditionally, they are packed into a namespace.
    """

    def __init__(self, command_to_put_main_system : PutSystem, commands_to_put_subsystems : PutSystem ):

        ExecutionCommand.__init__(self)
        self.executionCommands = commands_to_put_subsystems + [ command_to_put_main_system ] 

        self._command_to_put_main_system = command_to_put_main_system
        self._commands_to_put_subsystems = commands_to_put_subsystems

    @property
    def command_to_put_main_system(self):
        return self._command_to_put_main_system


    def set_tracing_infrastructure(self, tracing_infrastructure):

        self._tracing_infrastructure = tracing_infrastructure
        
        # forward to the main system
        self._command_to_put_main_system.set_tracing_infrastructure( tracing_infrastructure )

        # forward to all subsystems
        for cmd in self._commands_to_put_subsystems:
            cmd.set_tracing_infrastructure( tracing_infrastructure )



    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: System with the API (" + self._command_to_put_main_system.API_name + " along with subsystems):")
        
        for c in self.executionCommands:
            c.print_execution()

        print(Style.BRIGHT + Fore.YELLOW + "}")
        
    def generate_code_init(self, language):

        for c in self.executionCommands:
            c.generate_code_init(language)        

    def generate_code_destruct(self, language):
        for c in self.executionCommands:
            c.generate_code_destruct(language)            

    def generate_code(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                pass

            if flag == 'code':
                #
        

                lines += '// namespace for ' + self._command_to_put_main_system.API_name + ' {\n'

                # put the global variables
                innerLines = '// global variables\n'

                for c in self.executionCommands:
                    innerLines += c.generate_code(language, 'variables')

                innerLines += '\n'

                # put the code
                for c in self.executionCommands:
                    innerLines += c.generate_code(language, 'code')

                lines += cgh.indent(innerLines)

                # end namespace (finish)
                lines += '// end of namespace for ' + self._command_to_put_main_system.API_name + '\n\n'


        return lines

