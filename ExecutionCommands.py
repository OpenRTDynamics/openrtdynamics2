from libdyn import *
from Signal import *
from Block import *
from irpar import *

from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)

from TraverseGraph import *



class ExecutionCommand:
    def __init__(self):

        pass


    def codeGen(self, language, flag):

        lines = ''

        return lines


class CommandCalculateOutputs(ExecutionCommand):

    def __init__(self, executionLine, targetSignals):
        # targetSignals is optional

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
                # TODO: exclude the input singals 
                for e in self.executionLine.getSignalsToExecute():

                    print('output codegen for ' +  e.toStr() )
                    lines += e.getSourceBlock().getBlockPrototype().codeGen('c++', 'localvar')


            if flag == 'code':
                # lines += '{\n'

                for e in self.executionLine.getSignalsToExecute():

                    print('output codegen for ' +  e.toStr() )
                    lines += e.getSourceBlock().getBlockPrototype().codeGen('c++', 'output')

        return lines


class CommandPublishResult(ExecutionCommand):

    #
    # Creates an API-function to return the calculated values
    # 

    def __init__(self, nameAPI : str, signals : List[ Signal ], executionCommands):

        self.signals = signals
        self.executionCommands = executionCommands
        self.nameAPI = nameAPI

        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: publish:")
        for s in self.signals:
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
                lines += '// calculate'
                for s in self.signals:
                    lines += ' ' + s.getName()

                lines += '\n'

                lines += self.nameAPI + '('
                for s in self.signals:
                    lines +=  ' double & '  + s.getName()

                lines +=  ' ) {\n'

                # put the local variables
                for c in self.executionCommands:
                    lines += c.codeGen(language, 'localvar')
                
                lines += '\n'

                # put the code
                for c in self.executionCommands:
                    lines += c.codeGen(language, 'code')

                # define the API-function (finish)
                lines += '}\n\n'


        return lines


class CommandUpdateStates(ExecutionCommand):

    def __init__(self, blockList):

        self.blockList = blockList
        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: update states of:")

        for block in self.blockList:
            print("  - " + block.toStr() )

        # self.executionLine.printExecutionLine()

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += ''
                for b in self.blockList:
                    lines += b.getBlockPrototype().codeGen('c++', 'update')

        return lines




class CommandCompondUpdateStates(ExecutionCommand):

    #
    # Creates an API-function to update the states
    # 

    def __init__(self, executionCommands):

        self.executionCommands = executionCommands
        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: updating the states as follows")
        print(Style.BRIGHT + Fore.YELLOW + "{")

        for c in self.executionCommands:
            c.printExecution()

        print(Style.BRIGHT + Fore.YELLOW + "}")
        

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'code':
                lines += 'updateStates() {\n'

                # TODO: ensure variables are not defined twice
                for c in self.executionCommands:
                    lines += c.codeGen(language, 'localvar')
                
                lines += '\n'

                for c in self.executionCommands:
                    lines += c.codeGen(language, 'code')

                lines += '}\n\n'

        return lines






class CommandCacheOutputs(ExecutionCommand):

    def __init__(self, signals : List[Signal]):

        self.signals = signals
        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: cache the following outputs (so that they do not need to be recalculated):")

        for s in self.signals:
            print("  - " + s.toStr() )

        # self.executionLine.printExecutionLine()

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':


            if flag == 'variables':
                lines += ''
                for s in self.signals:
                    cachevarName = s.getName() + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()

                    lines +=  '\n// cache for ' + s.getName() + '\n'
                    lines += 'double ' + cachevarName + " {NAN};" + '\n' 

            if flag == 'code':
                lines += ''
                for s in self.signals:
                    cachevarName = s.getName() + "__" + s.getSourceBlock().getBlockPrototype().getUniqueVarnamePrefix()
                    lines += cachevarName + ' = ' + s.getName() + '\n'

        return lines
