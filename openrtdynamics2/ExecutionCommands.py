from .libdyn import *
from .Signal import *
from .Block import *
from .TraverseSignalFlowGraph import *
from . import  CodeGenHelper as cgh

from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)

from textwrap import *
from string import Template




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

    def printExecution(self):
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

                            # s is a system output: the code that generates the source to calculate s shall not reserve memeory for s

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
                            # only implement caching for intermediate computaion results.
                            # I.e. exclude the simulation input signals

                            # print('create local variable for signal ' + s.name + ' / ' + s.toStr() )

                            if not s.is_referencing_memory:
                                lines += cgh.defineVariableLine( s )



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
        
    def printExecution(self):

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
        
    def printExecution(self):

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

    def printExecution(self):

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
        
    def printExecution(self):

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

        for e in executionCommands:
            e.setContext(self)


    @property
    def nameAPI(self):
        return self._nameAPI

        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: API outputs are:")
        for s in self.outputSignals:
            print(Style.DIM + '  - ' + s.name)

        print(Style.BRIGHT + Fore.YELLOW + "that are calculated by: {")
        
        for c in self.executionCommands:
            c.printExecution()

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

                    # put structs to hold I/O signals
                    lines += '// output data structure for ' + self._nameAPI + '\n'
                    tmp = cgh.defineVariables( self.outputSignals )
                    tmp = indent(tmp, '  ')
                    lines += f'struct Outputs_{ self._nameAPI }  {{\n{ tmp }}};\n\n'

                    lines += '// input data structure for ' + self._nameAPI + '\n'
                    tmp = cgh.defineVariables( self.inputSignals )
                    tmp = indent(tmp, '  ')
                    lines += f'struct Inputs_{ self._nameAPI }  {{\n{ tmp }}};\n\n'


                    #
                    # put a wrapper function that offers a 'nicer' API using structs for in- and output signals
                    #

                    # put function header
                    lines += '// wrapper function for ' + self._nameAPI + '\n'
                    lines += 'Outputs_' + self._nameAPI + ' ' + self._nameAPI + '__ (Inputs_' + self._nameAPI + ' inputs)\n'

                    if len(self.outputSignals) > 0 or len(self.inputSignals):

                        outputArguments = cgh.getStructElements( 'outputs' , self.outputSignals )
                        inputArguments = cgh.getStructElements( 'inputs' , self.inputSignals )

                        argumentsString = ''
                        if len(outputArguments) > 0:
                            argumentsString += ', '.join( outputArguments )

                        if len(outputArguments) > 0 and len(inputArguments) > 0:
                            argumentsString += '   ,   '                    

                        if len(inputArguments) > 0:
                            argumentsString += ', '.join( inputArguments )

                    else:
                        argumentsString = ''

                    lines += '{\n'

                    functionLines = ''
                    functionLines += cgh.defineStructVar( 'Outputs_' + self._nameAPI, 'outputs'  ) + '\n'

                    functionLines += '// call to wrapped function\n'
                    functionLines += self._nameAPI + '(' + argumentsString + ');\n'


                    functionLines += '\n'
                    functionLines += '// return the signals in a struct\n'
                    functionLines += 'return outputs;\n'

                    lines += indent(functionLines, '  ')
                    
                    lines += '}\n\n'
                else:
                    print()


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

        self._api_function_names = {'calculate_output' : self.outputCommand.nameAPI,
                         'state_update' : self.updateCommand.nameAPI,
                         'reset' : self.resetCommand.nameAPI }

        self._api_functions = {'calculate_output' : self.outputCommand,
                         'state_update' : self.updateCommand,
                         'reset' : self.resetCommand }


        self.system = system
        self.nameAPI = system.getName()

        for e in self.executionCommands:
            e.setContext(self)



    # def getAPI_name(self):
    #     return self.nameAPI

    @property
    def API_name(self):
        return self.nameAPI

    @property
    def API_functionNames(self):
        return self._api_function_names
        
    @property
    def API_functions(self):
        return self._api_functions

    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: Simulation with the API (" + self.nameAPI + "):")
        
        for c in self.executionCommands:
            c.printExecution()

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

                lines += cgh.indent(innerLines)

                # define the API-function (finish)
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

    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: System with the API (" + self._command_to_put_main_system.API_name + " along with subsystems):")
        
        for c in self.executionCommands:
            c.printExecution()

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

