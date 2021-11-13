from .system import *
from .signal_network.signals import *
from .signal_network import *
from .graph_traversion import *
from . import  code_generation_helper as cgh

from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)

from textwrap import *


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

class CodeGeneratorModule(object):
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
class CommandGenerateClusters(CodeGeneratorModule):
    """

    """

    def __init__(self, system, execution_plan, manifest, blocks):
        CodeGeneratorModule.__init__(self)

        self._system                     = system
        self.clusters                    = execution_plan.clusters
        self.execution_plan              = execution_plan
        self.outputs_info                = manifest.outputs_info
        self.state_info                  = manifest.state_info
        self.system_inputs               = manifest.system_inputs
        self.blocks                      = blocks

        # Hint: 
        #
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
        action_list = [ '_cluster_' + str(c.id) + '(inputs);' for c in self.clusters ]

        code_switch = cgh.cpp_generate_select( 'current_cluster_id', case_labels, action_list )


        code = """
void compute_cluster(Inputs const & inputs, int cluster_id) {

    // printf("compute_cluster: %d ", cluster_id);

    // init
    int current_cluster_id = cluster_id;

    while (true) {

        // look for dependencies
        bool ready_to_compute = true;

        for (int i = _cluster_counter[current_cluster_id]; i < _n_dependencies[current_cluster_id]; ++i ) {

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

        // printf("exe %d ", current_cluster_id);

        // mark cluster as executed
        _cluster_executed[current_cluster_id] = true;

        //
        if (current_cluster_id == cluster_id)
            break;

        // step back
        current_cluster_id = _step_back_cluster[current_cluster_id];
    }

    // printf("\\n");
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

                lines += ''
                lines += "\n\n// states\n"
                for b in self.blocks:
                    
                    #
                    # TODO: rename 'defStates' to 'variables'
                    #
                    
                    lines += b.getBlockPrototype().generate_code_defStates('c++')




            if flag == 'code':

                                # introduce a structure that combines all system inputs
                lines += '// all system inputs and outputs combined\n'
                lines += cgh.define_structure('Inputs', self.system_inputs)
                lines += cgh.define_structure('Outputs', self.outputs_info['output_signals'])



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

                
                for cluster in self.clusters:
                    
                    code_for_cluster = ''

                    code_for_cluster += '// needed input signal(s): ' + ', '.join( [s.name for s in cluster.dependency_signals_simulation_inputs] ) + '\n'
                    code_for_cluster += '// needed signal(s) from other clusters: ' + ', '.join( [s.name for s in cluster.dependency_signals_that_are_junctions] )  + '\n'
                    code_for_cluster += '// the target signal is ' + cluster.destination_signal.name  + '\n'
                    code_for_cluster += '\n'

                    # get input variables
                    code_for_cluster += '// input variables\n'
                    for s in cluster.dependency_signals_simulation_inputs:
                        code_for_cluster += cgh.defineVariable(s, make_a_reference=True, mark_const=True ) + ' = inputs.' + s.name + ';\n'

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

                    lines += cgh.cpp_define_generic_function(
                        '_cluster_' + str(cluster.id),
                        'void',
                        'Inputs const & inputs',
                        code_for_cluster
                    )

                    

                lines += self._code_for_dependency_tree()
                lines += '\n'

                #
                # generate output trigger function
                #

                self.output_signals = []

                for i, s in enumerate(self.outputs_info['output_signals']):

                    c = self.outputs_info['clusters'][i]

                    # mapping output signal to cluster that computes the variable: s -> c


                # int _output_signal_index_to_cluster_id[3] = { 0, 3, 4 };
                
                ilines = ''
                ilines += 'int _output_signal_index_to_cluster_id[' + str(len(self.outputs_info['output_signals'])) + '] = {' + ', '.join( [ str(c.id) for c in self.outputs_info['clusters'] ] ) + '};\n'
                ilines += 'compute_cluster( inputs, _output_signal_index_to_cluster_id[output_signal_index] );\n'

                lines += cgh.cpp_define_generic_function('compute_output', 'void', 'Inputs const & inputs, int output_signal_index', ilines)
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

 
                # get input variables
                ilines += '// input variables    TODO: find out how to handle direct system inputs to update the states\n'
                for s in self.state_info['input_signals']:
                    ilines += cgh.defineVariable(s, make_a_reference=True, mark_const=True ) + ' = inputs.' + s.name + ';\n'

                lines += '\n'

                # get target values of other clusters
                ilines += '// cluster target variables\n'
                for c in self.state_info['clusters']:

                    s = c.destination_signal

                    ilines += 'compute_cluster (inputs, ' + str(c.id) + ');\n'

                    ilines += cgh.defineVariable(s, make_a_reference=True ) + ' = _cluster_target_values.' + s.name + ';\n'

                lines += '\n'

                for b in self.state_info['blocks']:
                    ilines += '// update block ' + b.name + '\n'
                    ilines += b.getBlockPrototype().generate_code_update('c++')


                lines += cgh.cpp_define_generic_function('update', 'void', 'Inputs const & inputs', ilines)
                lines += '\n'


                #
                # define the generic step functions
                #

                function_code = ''
                function_code = '_reset_clusters();\n'

                # reset
                code_reset_states  = '// reset\nreset();'

                # outputs
                code_calc_output  = '// calc outputs\n'

                for c in self.outputs_info['clusters']:
                    code_calc_output += 'compute_cluster(inputs, ' + str(c.id) + ');\n'

                for c in self.outputs_info['clusters']:
                    code_calc_output += 'outputs.' + c.destination_signal.name + ' = _cluster_target_values.' + c.destination_signal.name + ';\n'


                code_update_states = '// update\n'
                #code_update_states += '_inputs = inputs; // set reference to input signals;\n'
                code_update_states += 'update(inputs);\n'

                # conditional update / output
                function_code += cgh.generate_if_else(language, condition_list=['reset_states'], action_list=[code_reset_states] )
                function_code += cgh.generate_if_else(language, condition_list=['calculate_outputs'], action_list=[code_calc_output] )
                function_code += cgh.generate_if_else(language, condition_list=['update_states'], action_list=[code_update_states] )
                function_code += '\n'

                #   
                inner_lines = '// main step function \n'                

                inner_lines += cgh.cpp_define_generic_function( 
                    fn_name='step', 
                    return_cpp_type_str = 'void', 
                    arg_list_str = 'Outputs & outputs, Inputs const & inputs, bool calculate_outputs, bool update_states, bool reset_states', 
                    code = function_code
                )
  
                lines += inner_lines



                pass

        return lines






class PutSystem(CodeGeneratorModule):
    """
        Represents a system that is represented by a class in c++
    """

    def __init__(
        self, 
        system : System,
        command_to_compute_clusters : CodeGeneratorModule,
    ):
        CodeGeneratorModule.__init__(self)
        self.executionCommands = [  command_to_compute_clusters ] 

        self.command_to_compute_clusters = command_to_compute_clusters


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
        
    # @property
    # def API_functions(self):
    #     return self._api_functions

    def print_execution(self):

        print(Style.BRIGHT + Fore.YELLOW + "CodeGeneratorModule: System with the API (" + self.nameAPI + "):")
        
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
                inner_lines += 'public:\n'
                inner_lines += cgh.cpp_define_generic_function(
                    fn_name=self.nameAPI,
                    return_cpp_type_str='',
                    arg_list_str='', code=''
                )

                #
                # put the local variables
                #

                inner_lines += '// variables\n'
                for c in self.executionCommands:
                    inner_lines += c.generate_code(language, 'variables')
                
                inner_lines += '\n'

                # put the code
                for c in self.executionCommands:
                    inner_lines += c.generate_code(language, 'code')


                # # define the API-function (finish)
                lines += cgh.indent(inner_lines)
                lines += '};\n\n'

        return lines






class PutSystemAndSubsystems(CodeGeneratorModule):
    """
        Represents a system and its subsystem togethter that is represented by multiple classes in c++.
        Aditionally, they are packed into a namespace.
    """

    def __init__(self, command_to_put_main_system : PutSystem, commands_to_put_subsystems : PutSystem ):

        CodeGeneratorModule.__init__(self)
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

        print(Style.BRIGHT + Fore.YELLOW + "CodeGeneratorModule: System with the API (" + self._command_to_put_main_system.API_name + " along with subsystems):")
        
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

