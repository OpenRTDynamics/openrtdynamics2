from typing import Dict, List

from .Block import Block
from .Signal import Signal, BlockOutputSignal
from . import CodeGenHelper as cgh


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

        Note: the number of outputs must be defined
    """

    def __init__(self, sim, inputSignals = None, N_outputs = None, output_datatype_list = None  ):

        self.block = Block(sim, self, inputSignals, blockname = None)

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

    def update_input_config(self, input_signals):
        """
            The input signal might be unknown on construction. 
        """
        self.block.update_input_config(input_signals)

    def update_output_datatypes(self, output_datatype_list : List [Signal] ):

        N_outputs = len(self._outputSignals)

        if not len(output_datatype_list) == N_outputs:
            raise BaseException("number of given datatypes does not match the number of outputs")

        for i in range(0, N_outputs):
            self._outputSignals[i].update_datatype_config( output_datatype_list[i] )



    def getUniqueVarnamePrefix(self):
        # return a variable name prefix unique in the simulation
        # to be used for code generation 
        return "block_" + self.block.name


    #
    # The derived classes shall use these shortcuts to access the I/O signals
    #

    @property
    def name(self):
        return self.block.name

    # TODO what's with this? remove this and replace with 'outputs'
    @property
    def outputSignals(self):
        return self._outputSignals

    @property
    def outputs(self):
        # return the output signals
        return self._outputSignals

    @property
    def inputs(self):
        return self.block.inputs


    # get a signal of a specific output port
    def outputSignal(self, port):
        #return self.block.getOutputSignals()[port]
        return self.block.getOutputSignal(port)

    # get a signal of a specific input port
    def inputSignal(self, port):
        return self.block.getInputSignal(port)


    #
    # Callback functions that should/could be re-implemented
    #

    def compile_callback_all_subsystems_compiled(self):
        """
            callback notifiing when all subsystems inside the system this block is placed into
            are compiled. Hence, it is possible to e.g. access subsystem data like the input
            array or the I/O datatypes, which might have not beed defined before.
        """

        pass

    def compile_callback_all_datatypes_defined(self):
        """
            callback notifiing when all datatypes are defined
        """

        # TODO: implement notification in compile process

        pass


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
            NOTE 8.4.2020: unused 

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

    def codeGen_constructor(self, language):
        return ''
        
    def codeGen_destructor(self, language):
        return ''
        
    def codeGen_output_list(self, language, signals : List [ Signal ] ):
        return '// WARNING: * unimplemented output computation *'
        
    def codeGen_update(self, language):
        return ''
        
    def codeGen_reset(self, language):
        return ''
        
        

