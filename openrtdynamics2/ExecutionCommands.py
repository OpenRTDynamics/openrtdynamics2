from .libdyn import *
from .Signal import *
from .Block import *
from .TraverseGraph import *
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

        # the upper level execution command within the execution tree
        # None by default
        self.contextCommand = None

    @property
    def treeLevel(self):
        return self.treeLevel_

    # set the parent execution command
    def setContext(self, context ):
        self.contextCommand = context
        self.treeLevel_ = context.treeLevel + 1

    def codeGen_init(self, language):
        # 
        raise BaseException('codeGen_init unimplemented')

    def codeGen_destruct(self, language):
        raise BaseException('codeGen_destruct unimplemented')
        pass

    def codeGen(self, language, flag):

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

    def __init__(self, system, executionLine, targetSignals, no_memory_for_output_variables : bool, output_signals = []):
        ExecutionCommand.__init__(self)

        self._system = system
        self.executionLine = executionLine
        self.targetSignals = targetSignals
        self._output_signals = output_signals
        self.define_variables_for_the_outputs = not no_memory_for_output_variables

    def printExecution(self):
        signalListStr = '['

        if self.targetSignals is not None:
            signalListStr += cgh.signalListHelper_names_string(self.targetSignals)

        signalListStr += ']'

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: follow output execution line to calculate " + signalListStr + " using:")

        self.executionLine.printExecutionLine()

    def codeGen_init(self, language):
        pass

    def codeGen_destruct(self, language):
        pass

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'localvar':

                # 
                SignalsExceptOutputs = self.executionLine.getSignalsToExecute().copy()

                # remove the system-output signals if requested
                if not self.define_variables_for_the_outputs: # This is flipped by its name
                    for s in self.targetSignals:

                        # if s is output signal of system 
                        if s in self._output_signals:

                            # s is a system output: the code that generates the source to calculate s shall not reserve memeory for s

                            SignalsExceptOutputs.remove( s )

                            # notify the block prototype that the signal s will be a system output
                            # and, hence, no memory shall be allocated for s (because the memory is already
                            # available)
                            s.getSourceBlock().getBlockPrototype().codeGen_setOutputReference('c++', s)


                # skip the input signals in this loop (as their variables are already defined by the function API)
                for s in SignalsExceptOutputs:

                    if not s.is_crossing_system_boundary(self._system): # TODO: Why is this needed?
                        # only implement caching for intermediate computaion results.
                        # I.e. exclude the simulation input signals

                        # print('create local variable for signal ' + s.name + ' / ' + s.toStr() )

                        lines += cgh.defineVariableLine( s )



            if flag == 'code':
                lines += '\n// calculating the block outputs in the following order ' + cgh.signalListHelper_names_string(self.executionLine.signalOrder ) + '\n'
                lines += '// that depend on ' + cgh.signalListHelper_names_string(self.executionLine.dependencySignals) + '\n'
                lines += '// dependencies that require a state update are ' + cgh.signalListHelper_names_string(self.executionLine.dependencySignalsThroughStates) + ' \n'
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
                    lines += block.getBlockPrototype().codeGen_output_list('c++', blocks_with_outputs_to_compute[ block ] )
                    
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

    def codeGen_init(self, language):
        pass

    def codeGen_destruct(self, language):
        pass

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += ''
                for b in self.blockList:
                    lines += b.getBlockPrototype().codeGen_reset('c++')

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

    def codeGen_init(self, language):
        pass

    def codeGen_destruct(self, language):
        pass

    def codeGen(self, language, flag):

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
                    
                    lines += b.getBlockPrototype().codeGen_defStates('c++')

            if flag == 'code':
                lines += '\n'
                lines += ''

                for b in self.blockList:
                    lines += b.getBlockPrototype().codeGen_update('c++')


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

    def codeGen_init(self, language):
        pass

    def codeGen_destruct(self, language):
        pass

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':


            if flag == 'variables':
                lines += ''
                lines += "\n\n//\n// cached output values\n//\n"
                for s in self.signals:

                    cachevarName = s.name + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()

                    lines +=  '\n// cache for ' + s.name + '\n'
                    lines +=  s.getDatatype().cppDataType + ' ' + cachevarName + "; // put NAN!" + '\n' 

            if flag == 'code':
                lines += '\n'
                lines += '// saving the signals ' + cgh.signalListHelper_names_string(self.signals) + ' into the states \n'
                lines += '\n'


                for s in self.signals:

                    cachevarName = s.name + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()
                    lines += cachevarName + ' = ' + s.name + ';\n'

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

    def codeGen_init(self, language):
        pass

    def codeGen_destruct(self, language):
        pass

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += '\n'
                lines += '// restoring the signals ' + cgh.signalListHelper_names_string(self.signals) + ' from the states \n'
                lines += '\n'

                for s in self.signals:

                    cachevarName = s.name + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()
                    lines +=  s.getDatatype().cppDataType + ' ' + s.name + ' = ' + cachevarName + ";" + '\n' 

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
        
    def codeGen_init(self, language):
        for c in self.executionCommands:
            c.codeGen_init(language)

    def codeGen_destruct(self, language):
        for c in self.executionCommands:
            c.codeGen_destruct(language)

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                for c in self.executionCommands:
                    lines += c.codeGen(language, 'variables')


            if flag == 'code':
                #
                # ------ define the API-function ------
                #
                if len(self.outputSignals) > 0:
                    lines += '// API-function ' + self._nameAPI + ' to compute: ' + cgh.signalListHelper_names_string( self.outputSignals )  #  ' '.join( cgh.signalListHelper_names( self.outputSignals ) )
                else:
                    lines += '// API-function' + self._nameAPI

                lines += '\n'
                lines += 'void ' + self._nameAPI + '('

                # put the parameter list e.g. double & y1, double & y2, u1, u2
                elements = []
                for s in self.outputSignals:
                    elements.append( s.getDatatype().cppDataType + ' & '  + s.name )
                    
                elements.extend( cgh.signalListHelper_CppVarDefStr( self.inputSignals ) )

                lines += ', '.join(elements)
                lines +=  ') {\n'

                # innerLines will be indented
                innerLines = ''
                
                # put the local variables
                for c in self.executionCommands:
                    innerLines += c.codeGen(language, 'localvar')
                
                innerLines += '\n'

                # put the code
                for c in self.executionCommands:
                    innerLines += c.codeGen(language, 'code')

                lines += indent(innerLines, '  ')

                # define the API-function (finish)
                lines += '}\n\n'

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

                    innerLines = ''
                    innerLines += cgh.defineStructVar( 'Outputs_' + self._nameAPI, 'outputs'  ) + '\n'

                    innerLines += '// call to wrapped function\n'
                    innerLines += self._nameAPI + '(' + argumentsString + ');\n'


                    innerLines += '\n'
                    innerLines += '// return the signals in a struct\n'
                    innerLines += 'return outputs;\n'

                    lines += indent(innerLines, '  ')
                    
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
        
    def codeGen_init(self, language):

        for c in self.executionCommands:
            c.codeGen_init(language)

        # call init codegen for each block in the simulation
        for block in self.system.blocks:
            block.getBlockPrototype().codeGen_init(language)


    def codeGen_destruct(self, language):
        for c in self.executionCommands:
            c.codeGen_destruct(language)

    def codeGen(self, language, flag):

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
                    innerLines += c.codeGen(language, 'variables')
                
                innerLines += '\n'

                # put the code
                for c in self.executionCommands:
                    innerLines += c.codeGen(language, 'code')

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
        
    def codeGen_init(self, language):

        for c in self.executionCommands:
            c.codeGen_init(language)        

    def codeGen_destruct(self, language):
        for c in self.executionCommands:
            c.codeGen_destruct(language)            

    def codeGen(self, language, flag):

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
                    innerLines += c.codeGen(language, 'variables')

                innerLines += '\n'

                # put the code
                for c in self.executionCommands:
                    innerLines += c.codeGen(language, 'code')

                lines += cgh.indent(innerLines)

                # end namespace (finish)
                lines += '// end of namespace for ' + self._command_to_put_main_system.API_name + '\n\n'


        return lines

