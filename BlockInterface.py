from typing import Dict, List

from Block import *
from Signal import *
from Datatypes import *
from SignalInterface import *

class BlockPrototype(object):
    """
        This is a base class to be deviated from each block type.
        It contains logic to handle the input/ output types and
        the parameters.

        Herein, all technical stuff shall be hidden from the user and
        the one, how, implements new blocks.
    """

    def __init__(self, sim, inputSignals, nOutputs ):

        # unwrap the input signals
        # inputSignalsUnwrapped = []
        #for i in range(0, len( inputSignals )):
        #    inputSignalsUnwrapped.append( inputSignals[i].unwrap )

        self.block = Block(sim, self, inputSignals, blockname = '')

        self._outputSignals = []
        for i in range(0,nOutputs):
            self._outputSignals.append( BlockOutputSignal(sim, None, self.block, sourcePort=i  ) )

        self.block.configOutputSignals( self._outputSignals )


    def getUniqueVarnamePrefix(self):
        # return a variable name prefix unique in the simulation
        # to be used for code generation 
        return "" + self.block.getName() +  "_" + str(self.block.id)


    #
    # The derived classes shall use these shortcuts to access the I/O signals
    #

    # TODO what's with this? remove this and replace with 'outputs'
    @property
    def outputSignals(self):
        return self._outputSignals

    @property
    def outputs(self):
        # return the output signals
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

    def codeGen_init(self, language):
        """
            called to when the code generator initializes and before code is generated
        """
        pass

    def codeGen_destruct(self, language):
        """
            called when code generation has finished finished
        """
        pass

    def configDefineOutputTypes(self, inputTypes):
        raise BaseException("configDefineOutputTypes not implemented")

    def codeGen_setOutputReference(self, language, signal):
        """
            infcates that for the given signal no local variable will be reserved by calling codeGen_localvar.
            Insted the variable to store the signal is an output of the system and has been already defined.
        """
        pass

    def codeGen_defStates(self, language):
        return ''

    def codeGen_localvar(self, language, signal : Signal):
        return ''
        
    def codeGen_constructor(self, language):
        return ''
        
    def codeGen_destructor(self, language):
        return ''
        
    def codeGen_output(self, language, signal : Signal):
        return ''
        
    def codeGen_update(self, language):
        return ''
        
    def codeGen_reset(self, language):
        return ''
        
        

