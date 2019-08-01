from typing import Dict, List

from Block import *
from Signal import *
from Datatypes import *
from SignalInterface import *

class BlockPrototype:
    """
        This is a base class to be deviated from each block type.
        It contains logic to handle the input/ output types and
        the parameters.

        Herein, all technical stuff shall be hidden from the user and
        the one, how, implements new blocks.
    """

    def __init__(self, sim, inputSignals, nOutputs ):

        self.block = Block(sim, self, inputSignals, blockname = '')

        self._outputSignals = []
        for i in range(0,nOutputs):
            self._outputSignals.append( BlockOutputSignalUser(sim, None, self.block, sourcePort=i  ) )

        self.block.configOutputSignals( self._outputSignals )


    def getUniqueVarnamePrefix(self):
        # return a variable name prefix unique in the simulation
        # to be used for code generation 
        return "" + self.block.getName() +  "_" + str(self.block.getBlockId())


    #
    # The derived classes shall use these shortcuts to access the I/O signals
    #

    @property
    def outputSignals(self):
        return self._outputSignals

    # get a signal of a specific output port
    def outputSignal(self, port):
        #return self.block.getOutputSignals()[port]
        return self.block.getOutputSignal(port)

    # get a signal of a specific input port
    def inputSignal(self, port):
        return self.block.getInputSignal(port)


    #
    # Standard functions that should be re-implemented
    #

    def configDefineOutputTypes(self, inputTypes):
        raise BaseException("configDefineOutputTypes not implemented")

    # function to generate code
    def codeGen(self, language, flag):
        # raise BaseException("code generation not implemented")

        # This is to show what could be implemented
        lines = ''

        if language == 'c++':

            if flag == 'defStates':
                lines = ''

            elif flag == 'localvar':
                lines = ''

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = ''

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''

        return lines

    def codeGen_defStates(self, language):
        return ''

    def codeGen_localvar(self, language):
        return ''
        
    def codeGen_constructor(self, language):
        return ''
        
    def codeGen_destructor(self, language):
        return ''
        
    def codeGen_output(self, language):
        return ''
        
    def codeGen_update(self, language):
        return ''
        
    def codeGen_reset(self, language):
        return ''
        
        

