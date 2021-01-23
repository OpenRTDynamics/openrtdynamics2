from .libdyn import *
from .signals import *
from .Block import *
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

    def __init__(self, nameAPI : str, inputSignals : List[ Signal ], outputSignals : List[ Signal ], executionCommands, generate_wrappper_functions = True):
        ExecutionCommand.__init__(self)

        self.outputSignals = outputSignals
        self.inputSignals = inputSignals
        self.executionCommands = executionCommands
        self._nameAPI = nameAPI
        self._generate_wrappper_functions = generate_wrappper_functions

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
                    function_code += cgh.create_printf(intro_string='ENTR: ' + self.contextCommand.API_name + '/' + self.nameAPI, 
                                                    signals=self.inputSignals)

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
                    function_code += cgh.create_printf(intro_string='EXIT: ' + self.contextCommand.API_name + '/' + self.nameAPI, 
                                                    signals=self.outputSignals)

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

    def __init__(self, system : Simulation, resetCommand : PutAPIFunction, updateCommand : PutAPIFunction, outputCommand : PutAPIFunction ):
        ExecutionCommand.__init__(self)
        self.executionCommands = [ resetCommand, updateCommand, outputCommand  ] 

        self.resetCommand = resetCommand
        self.updateCommand = updateCommand
        self.outputCommand = outputCommand

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

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: Simulation with the API (" + self.nameAPI + "):")
        
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

                # put the local variables
                innerLines = '// variables\n'
                innerLines = 'public:\n'
                for c in self.executionCommands:
                    innerLines += c.generate_code(language, 'variables')
                
                innerLines += '\n'

                # put the code
                for c in self.executionCommands:
                    innerLines += c.generate_code(language, 'code')


                #
                # define the generic step functions
                #

                config_pass_by_reference = True

                all_input_signals = list(set(self.resetCommand.inputSignals + self.updateCommand.inputSignals + self.outputCommand.inputSignals))
                all_output_signals = self.outputCommand.outputSignals

                # introduce a structure that combines all system inputs
                innerLines += '// all system inputs and outputs combined\n'
                innerLines += cgh.define_structure('Inputs', all_input_signals)
                innerLines += cgh.define_structure('Outputs', all_output_signals)

                #
                # put a wrapper function that offers a 'nicer' API using structures for in- and output signals
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
                innerLines += '// main step function \n'

                if config_pass_by_reference:
                    innerLines += cgh.cpp_define_generic_function( 
                        fn_name='step', 
                        return_cpp_type_str = 'void', 
                        arg_list_str = 'Outputs & outputs, Inputs const & inputs, int calculate_outputs, bool update_states, bool reset_states', 
                        code = function_code
                    )
                else:
                    innerLines += cgh.cpp_define_generic_function( 
                        fn_name='step', 
                        return_cpp_type_str = 'Outputs', 
                        arg_list_str = 'Inputs inputs, int calculate_outputs, bool update_states, bool reset_states', 
                        code = function_code
                    )




                # define the API-function (finish)
                lines += cgh.indent(innerLines)
                lines += '};\n\n'

        return lines






class PutSystemAndSubsystems(ExecutionCommand):
    """
        Represents a system and its subsystem togehter that is represented by multiple classes in c++.
        Addiitionally, they are packed into a namespace.
    """

    def __init__(self, command_to_put_main_system : PutSystem, commands_to_put_subsystems : PutSystem ):

        ExecutionCommand.__init__(self)
        self.executionCommands = commands_to_put_subsystems + [ command_to_put_main_system ] 

        self._command_to_put_main_system = command_to_put_main_system
        self._commands_to_put_subsystems = commands_to_put_subsystems

    @property
    def command_to_put_main_system(self):
        return self._command_to_put_main_system

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

