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

        sim                     - the system the block shall belong to
        inputSignals            - a list of input signals
        N_outputs               - prepare a number of nOutputs (optional in case output_datatype_list is given)
        output_datatype_list    - a list of datetypes for each output (optional)

    """

    def __init__(self, sim, inputSignals, N_outputs, output_datatype_list = None  ):

        self.block = Block(sim, self, inputSignals, blockname = '')

        # detect the number of outputs
        if N_outputs is None:
            if output_datatype_list is not None:
                N_outputs = len(output_datatype_list)
            else:
                BaseException("unable to determine the number of output ports")

        # create the outputs
        self._outputSignals = []
        for i in range(0, N_outputs):

            if output_datatype_list is None:
                datatype = None
            else:
                datatype = output_datatype_list[i]

            self._outputSignals.append( BlockOutputSignal(sim, datatype, self.block, sourcePort=i  ) )

        self.block.configOutputSignals( self._outputSignals )

    #
    # TODO: allow connecting the inputs after creating a prototype instance using this function
    #
    def connectInputs(self, inputSignals):
        pass


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
            indicates that for the given signal no local variable will be reserved by calling codeGen_localvar.
            Insted the variable to store the signal is an output of the system and has been already defined.
        """
        pass

    def codegen_addToNamespace(self, language):
        """
            Add code within the same namespace the block sits in.
            E.g. to add helper functions, classes, ...
        """
        return ''

    def codeGen_defStates(self, language):
        """
            to define discrete-time states of the block
        """

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
        
        

