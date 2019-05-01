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

    def __init__(self, executionLine):

        self.executionLine = executionLine
        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: calc outputs using:")

        self.executionLine.printExecutionLine()

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'begin':
                lines = ''

            if flag == 'end':
                lines = ''

        return lines


class CommandPublishResult(ExecutionCommand):

    def __init__(self, signal):

        self.signal = signal
        
    def printExecution(self):

        print(Style.BRIGHT + Fore.YELLOW + "ExecutionCommand: publish result of " + self.signal.toStr() )

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'begin':
                lines = ''

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
                lines = ''

            if flag == 'end':
                lines = ''

        return lines

