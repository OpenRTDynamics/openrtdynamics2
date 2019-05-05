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

            if flag == 'begin':
                # lines += '{\n'

                for e in self.executionLine.getSignalsToExecute():

                    print('output codegen for ' +  e.toStr() )
                    lines += e.getSourceBlock().getBlockPrototype().codeGen('c++', 'output')


            if flag == 'end':
                # lines = '}\n'
                pass

        return lines


class CommandPublishResult(ExecutionCommand):

    # TODO signal should be a list of signals
    def __init__(self, signal, executionCommand):

        self.signal = signal
        self.executionCommand = executionCommand
        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: publish result of " + self.signal.toStr() + " that is calculated by")
        print(Style.BRIGHT + Fore.YELLOW + "{")
        self.executionCommand.printExecution()
        print(Style.BRIGHT + Fore.YELLOW + "}")
        

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'begin':
                lines += '// calculate ' + self.signal.getName() + '\n'
                lines += 'calcPrimaryResults() {\n'

                lines += self.executionCommand.codeGen(language, 'begin')

                lines += '}\n\n'

            if flag == 'end':
                lines = ''

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

            if flag == 'begin':
                lines += ''
                for b in self.blockList:
                    lines += b.getBlockPrototype().codeGen('c++', 'update')

            if flag == 'end':
                lines = ''

        return lines




class CommandCompondUpdateStates(ExecutionCommand):

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

            if flag == 'begin':
                lines += 'updateStates() {\n'

                for c in self.executionCommands:
                    lines += c.codeGen(language, 'begin')

                lines += '}\n\n'

            if flag == 'end':
                lines = ''

        return lines