from libdyn import *
from Signal import *
from Block import *
from irpar import *
from TraverseGraph import *
from CodeGenHelper import *

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


    def codeGen(self, language, flag):

        lines = ''

        return lines


class CommandCalculateOutputs(ExecutionCommand):
    """
        execute an executionLine i.e. call the output-flags of all blocks given in executionLine
        in the correct order. This calculates the blocks outputs indicated by the signals given
        in executionLine.getSignalsToExecute()
    """

    def __init__(self, executionLine, targetSignals, defineVarsForOutputs : bool):
        ExecutionCommand.__init__(self)

        # targetSignals is optional
        self.defineVarsForOutputs = defineVarsForOutputs

        self.executionLine = executionLine
        self.targetSignals = targetSignals
        
    def printExecution(self):

        # make a string from a list of signals --> move to a function
        signalListStr = '['

        if self.targetSignals is not None:

            i = 0
            for s in self.targetSignals:
                signalListStr += s.getName()
                
                if i == len(self.targetSignals) - 1:
                    break

                signalListStr += ", "
                i += 1
                
        signalListStr += ']'

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: follow output execution line to calculate " + signalListStr + " using:")

        self.executionLine.printExecutionLine()

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'localvar':
                
                SignalsWithoutOutputs = self.executionLine.getSignalsToExecute()

                # remove the output signals if requested
                if self.defineVarsForOutputs:
                    for s in self.targetSignals:
                        SignalsWithoutOutputs.remove( s )

                # remove the input signals in this loop
                for s in SignalsWithoutOutputs:

                    if isinstance(s, BlockOutputSignal):
                        # only implement caching for intermediate computaion results.
                        # I.e. exclude the simulation input signals

                        print('output codegen to store the result ' +  s.toStr() )
                        lines += s.getSourceBlock().getBlockPrototype().codeGen('c++', 'localvar') # TODO: remove
                        # lines += s.getSourceBlock().getBlockPrototype().codeGen_localvar('c++')

                        # TODO: this should be:
                        lines += s.getSourceBlock().getBlockPrototype().codeGen_localvar('c++', s)



            if flag == 'code':
                # lines += '{\n'

                for s in self.executionLine.getSignalsToExecute():

                    if isinstance(s, BlockOutputSignal):
                        # only implement caching for intermediate computaion results.
                        # I.e. exclude the simulation input signals

                        print('output codegen to calculate ' +  s.toStr() )
                        lines += s.getSourceBlock().getBlockPrototype().codeGen('c++', 'output') # TODO: remove
                        # lines += s.getSourceBlock().getBlockPrototype().codeGen_output('c++')

                        # TODO: this should be:
                        lines += s.getSourceBlock().getBlockPrototype().codeGen_output('c++', s)

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

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += ''
                for b in self.blockList:
                    lines += b.getBlockPrototype().codeGen('c++', 'reset') # TODO: remove
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
                    
                    lines += b.getBlockPrototype().codeGen('c++', 'defStates') # TODO: remove
                    lines += b.getBlockPrototype().codeGen_defStates('c++')

            if flag == 'code':
                lines += ''
                for b in self.blockList:
                    lines += b.getBlockPrototype().codeGen('c++', 'update') # TODO: remove
                    lines += b.getBlockPrototype().codeGen_update('c++')

            # if flag == 'codereset':
            #     lines += ''
            #     for b in self.blockList:
            #         lines += b.getBlockPrototype().codeGen('c++', 'reset')

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

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':


            if flag == 'variables':
                lines += ''
                lines += "\n\n// cached output values\n"
                for s in self.signals:

                    cachevarName = s.getName() + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()

                    lines +=  '\n// cache for ' + s.getName() + '\n'
                    lines +=  s.getDatatype().cppDataType + ' ' + cachevarName + "; // put NAN!" + '\n' 

            if flag == 'code':
                lines += ''
                for s in self.signals:

                    cachevarName = s.getName() + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()
                    lines += cachevarName + ' = ' + s.getName() + ';\n'

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


    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += '\n'
                lines = '// restore cached signals\n'

                for s in self.signals:

                    cachevarName = s.getName() + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()
                    lines +=  s.getDatatype().cppDataType + ' ' + s.getName() + ' = ' + cachevarName + ";" + '\n' 

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

    def __init__(self, nameAPI : str, inputSignals : List[ Signal ], outputSignals : List[ Signal ], executionCommands):
        ExecutionCommand.__init__(self)

        self.outputSignals = outputSignals
        self.inputSignals = inputSignals
        self.executionCommands = executionCommands
        self._nameAPI = nameAPI

        for e in executionCommands:
            e.setContext(self)


    @property
    def nameAPI(self):
        return self._nameAPI

        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: API outputs are:")
        for s in self.outputSignals:
            print(Style.DIM + '  - ' + s.getName())

        print(Style.BRIGHT + Fore.YELLOW + "that are calculated by: {")
        
        for c in self.executionCommands:
            c.printExecution()

        print(Style.BRIGHT + Fore.YELLOW + "}")
        

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                for c in self.executionCommands:
                    lines += c.codeGen(language, 'variables')


            if flag == 'code':
                # define the API-function (start)
                lines += '// calculate ' + ' '.join( signalListHelper_names( self.outputSignals ) )
                
                lines += '\n'
                lines += 'void ' + self._nameAPI + '('

                # put the parameter list e.g. double & y1, double & y2, u1, u2
                elements = []
                for s in self.outputSignals:
                    elements.append( s.getDatatype().cppDataType + ' & '  + s.getName() )
                    
                elements.extend( signalListHelper_CppVarDefStr( self.inputSignals ) )

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

                # put structs to hold I/O signals
                lines += '// output data structure for ' + self._nameAPI + '\n'
                tmp = defineVariables( self.outputSignals )
                tmp = indent(tmp, '  ')
                lines += f'struct Outputs_{ self._nameAPI }  {{\n{ tmp }}};\n\n'

                lines += '// input data structure for ' + self._nameAPI + '\n'
                tmp = defineVariables( self.inputSignals )
                tmp = indent(tmp, '  ')
                lines += f'struct Inputs_{ self._nameAPI }  {{\n{ tmp }}};\n\n'


                #
                # put a wrapper function that offers an API using structs for in- and output signals
                #

                # put function header
                lines += '// wrapper function for ' + self._nameAPI + '\n'
                lines += 'Outputs_' + self._nameAPI + ' ' + self._nameAPI + '__ (Inputs_' + self._nameAPI + ' inputs)\n'

                if len(self.outputSignals) > 0 or len(self.inputSignals):

                    outputArguments = getStructElements( 'outputs' , self.outputSignals )
                    inputArguments = getStructElements( 'inputs' , self.inputSignals )

                    argumentsString = ''
                    if len(outputArguments) > 0:
                        argumentsString += ', '.join( outputArguments )

                    if len(outputArguments) > 0 and len(inputArguments) > 0:
                        argumentsString += '   ,   '                    

                    if len(inputArguments) > 0:
                        argumentsString += ', '.join( inputArguments )

                    print( 'args are: ' + argumentsString )

                else:
                    argumentsString = ''

                lines += '{\n'

                innerLines = ''
                innerLines += defineStructVar( 'Outputs_' + self._nameAPI, 'outputs'  ) + '\n'

                innerLines += '// call to wrapped function\n'
                innerLines += self._nameAPI + '(' + argumentsString + ');\n'


                innerLines += '\n'
                innerLines += '// return the signals in a struct\n'
                innerLines += 'return outputs;\n'

                lines += indent(innerLines, '  ')
                
                lines += '}\n\n'


        return lines







class PutSimulation(ExecutionCommand):
    """
        Represents a simulation that is represented by a class in c++
    """

    def __init__(self, nameAPI: str, resetCommand : ExecutionCommand, updateCommand : ExecutionCommand, outputCommand : ExecutionCommand ):
        ExecutionCommand.__init__(self)

        self.resetCommand = resetCommand
        self.updateCommand = updateCommand
        self.outputCommand = outputCommand

        self._api_function_names = {'calculate_output' : self.outputCommand.nameAPI,
                         'state_update' : self.updateCommand.nameAPI,
                         'reset' : self.resetCommand.nameAPI }

        self._api_functions = {'calculate_output' : self.outputCommand,
                         'state_update' : self.updateCommand,
                         'reset' : self.resetCommand }

        self.executionCommands = [ resetCommand, updateCommand, outputCommand  ] 


        self.nameAPI = nameAPI

        for e in self.executionCommands:
            e.setContext(self)



    def getAPI_name(self):
        return self.nameAPI

    @property
    def API_functionNames(self):
        return self._api_function_names
        
    @property
    def API_functions(self):
        return self._api_functions

    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: Simulation with the API:")
        
        for c in self.executionCommands:
            c.printExecution()

        print(Style.BRIGHT + Fore.YELLOW + "}")
        

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'variables':
                pass

            if flag == 'code':
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

                lines += indent(innerLines, '  ')

                # define the API-function (finish)
                lines += '};\n\n'


        return lines






