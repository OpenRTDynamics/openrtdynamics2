from typing import Dict, List

from .libdyn import *
from .Block import Block
from .signals import Signal, BlockOutputSignal
from . import code_generation_helper as cgh


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
                # the datatype for the output signal number i is already given and the block will 
                # be configured accordingly
                datatype = output_datatype_list[i]

            self._outputSignals.append( BlockOutputSignal(sim, datatype, self.block, sourcePort=i  ) )


        self.block.configOutputSignals( self._outputSignals )

    def update_input_config(self, input_signals):
        """
            The input signal might be unknown on construction. 
        """
        self.block.update_input_config(input_signals)


    def getUniqueVarnamePrefix(self):
        # return a variable name prefix unique in the simulation
        # to be used for code generation 
        return "block_" + self.block.name

    #
    # shortcuts to be used by derived classes
    #

    @property
    def name(self):
        return self.block.name

    @property
    def id(self):
        return self.block.id

    # The derived classes shall use these shortcuts to access the I/O signals
    @property
    def outputs(self):
        # return the output signals
        return self._outputSignals

    @property
    def inputs(self):
        return self.block.inputs

    #
    # Callback functions that should/could be re-implemented
    #

    # config
    def config_request_define_output_types(self, inputTypes):
        raise BaseException("config_request_define_output_types not implemented")

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        """
            returns a list of input signals on which the given output signal depends on with a direct feedforward
        """
        raise BaseException('BlockPrototype: config_request_define_feedforward_input_dependencies not defined')

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        """
            returns a list of input signals that are required to update the states
            that are required to further compute outputSignal
        """
        raise BaseException('BlockPrototype: config_request_define_state_update_input_dependencies not defined')

    # compile callbacks
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

    # code generation callback requests
    def generate_code_init(self, language):
        """
            called to when the code generator initializes and before code is generated
        """
        pass

    def generate_code_destruct(self, language):
        """
            called when code generation has finished finished
        """
        pass


    def generate_code_setOutputReference(self, language, signal):
        """
            indicates that for the given signal no local variable will be reserved by calling generate_code_localvar.
            Insted the variable to store the signal is an output of the system and has been already defined.
        """
        pass

    def codegen_addToNamespace(self, language):
        """
            Add code within the same namespace the block sits in.
            E.g. to add helper functions, classes, ...
        """
        return ''

    def generate_code_defStates(self, language):
        """
            to define discrete-time states of the block
        """
        return ''

    def generate_code_constructor(self, language):
        return ''
        
    def generate_code_destructor(self, language):
        return ''
        
    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        return '// WARNING: * unimplemented output computation *'
        
    def generate_code_update(self, language):
        return ''
        
    def generate_code_reset(self, language):
        return ''
        


    # TODO what's with this? remove this and replace with 'outputs'
    # @property
    # def outputSignals(self):
    #     return self._outputSignals
    #
    # TODO: remove these
    #
    # get a signal of a specific output port
    # def outputSignal(self, port):
    #     #return self.block.getOutputSignals()[port]
    #     return self.block.getOutputSignal(port)

    # # get a signal of a specific input port
    # def inputSignal(self, port):
    #     return self.block.getInputSignal(port)


    # def update_output_datatypes(self, output_datatype_list : List [Signal] ):

    #     N_outputs = len(self._outputSignals)

    #     if not len(output_datatype_list) == N_outputs:
    #         raise BaseException("number of given datatypes does not match the number of outputs")

    #     for i in range(0, N_outputs):
    #         self._outputSignals[i].update_datatype_config( output_datatype_list[i] )

        


#
# block templates for common use-cases
#

class StaticSource_To1(BlockPrototype):
    """
        This defines a static source
    """
    def __init__(self, sim : Simulation, datatype ):

        self.outputType = datatype

        BlockPrototype.__init__(self, sim, [], 1)

        # output datatype is fixed
        self.outputs[0].setDatatype(datatype)

    def config_request_define_output_types(self, inputTypes):

        # define the output type 
        return [ self.outputType ]

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on nothing
        return []

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states



class DynamicSource_To1(StaticSource_To1):
    """
        This defines a dynamic source
    """
    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return [] # indicates state dependency but these states do not depend on external signals



class StaticFn_1To1(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal ):

        self.u = u
        self.outputType = None

        BlockPrototype.__init__(self, sim, [ u ], 1)

    def config_request_define_output_types(self, inputTypes):

        # just inherit the input type 

        # TODO: 19.4.2020: kick out the uneeded None tests

        if inputTypes[0] is not None:
            self.outputType = inputTypes[0]
        else:
            self.outputType = None

        return [ self.outputType ]        

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on the only one input signals
        return [ self.u ]

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states




class StaticFn_NTo1(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : List[Signal] ):

        self.inputSignals = inputSignals

        BlockPrototype.__init__(self, sim, inputSignals, 1)

    def config_request_define_output_types(self, inputTypes):

        # check if the output signal type is already defined (e.g. by the user)
        if self.outputs[0].getDatatype() is None:
            #
            # no output type defined so far..
            # look for an already defined input type and inherit that type.
            #

            self.outputType = common_numeric_type(inputTypes)

        # return a proposal for an output type. 
        return [self.outputType]

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output (there is only one) depends on all inputs
        return self.inputSignals 

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states



