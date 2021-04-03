from .diagram_core.system import System
from .diagram_core import datatypes as dt
from .diagram_core.signal_network.signals import Signal
from .diagram_core import code_generation_helper as cgh
from . import block_interface as bi
from .block_prototypes_subsystems import *



class SingleSubsystemEmbedder(bi.BlockPrototype):
    """
        Prototype for a block that includes one sub-system
          (this is class to be derived, e.g. by XX, XX)

        - control_inputs                        - inputs used to control the execution (e.g. the condition for if)
        - subsystem_wrapper                     - the prototypes the subsystem (of type SystemWrapper)
        - reference_outputs                     - output signals of the reference subsystem from which the output datatypes are inherited
        - number_of_control_outputs             - the number of outputs of the subsystem used to control execution

        - helper function for code generation -

        - XX

                         
                        +--------------------------------------------------+  OutputMapEmbeddingBlockToSubsystem maps the outputs
                        | SingleSubsystemEmbedder (embedding block)        |  s1 --> se1, s2 --> se2
                        |                       +-------------+            |  
        normal input 1  |                       |             |            |  normal output 1 (s1)
                     +------------------------->+        (se1)+--------------->
                        |                       |   embedded  |            |
        normal input 2  |                       |             |            |  normal output 2   (self.normal_outouts)
                     +------------------------->+        (se2)+---------------> (s2)
                        |                       |  subsystem  |            |
                        |        control status |             | control    |
                        |            +--------->+             +-----+      |
                        |            |          |             | output(s)  |
                        |            |          +-------------+     |      |
                        |            |                              |      |-->
                        |     +------+------+                       |      | self.control_outputs (unused/future)
        control input(s)|     |  execution  |                       |      |
                     +------->+  control for+<----------------------+      |
                        |     |  subsystem  |                              |
                        |     +-------------+                              |
                        |                                                  |
                        +--------------------------------------------------+

        Figure drawn with http://asciiflow.com/



        lists of output signals
        -----------------------

        self.outputs                                           - all outputs of the embeding block
        self.subsystem_wrapper.outputs                         - all outputs of the subsystem that are initially present
        self.subsystem_wrapper.compile_result.outputSignals    - all outputs of the subsystem that are present after compilation
        signals (parameter for generate_code_output_list)      - outputs out of self.outputs that need to be computed

        Number of outputs
        -----------------
        self.number_of_normal_outputs
        self.number_of_control_outputs
        self.total_number_of_subsystem_outputs

    """
    def __init__(self, sim : System, control_inputs : List [Signal], subsystem_wrapper : SystemWrapper, number_of_control_outputs : int = 0 ):

        # the prototypes of the subsystem
        self._subsystem_wrapper = subsystem_wrapper
        
        # analyze the default subsystem (the first) to get the output datatypes to use
        reference_subsystem = self._subsystem_wrapper

        # the number of outputs besides the subsystems outputs
        self.number_of_control_outputs = number_of_control_outputs

        self.total_number_of_subsystem_outputs = len(reference_subsystem.outputs)
        self.number_of_normal_outputs = len(self._subsystem_wrapper.outputs) - number_of_control_outputs

        if self.number_of_normal_outputs < 0:
            raise BaseException("The number of control outputs is bigger than the total number of outputs provided by the subsystem.")

        self._number_of_outputs_of_all_nested_systems = len(reference_subsystem.outputs)



        # now call the constructor for block prototypes and make input and output signals available
        bi.BlockPrototype.__init__(self, sim=sim, inputSignals=None, N_outputs = self.number_of_normal_outputs )



        # control inputs that are used to control how the subsystems are handled
        self._control_inputs = control_inputs 

        # a list of all inputs including self._list_of_all_subsystem_inputs and self._control_inputs
        # will be filled in on compile_callback_all_subsystems_compiled()
        self._list_of_all_inputs = None



        # inherit output datatypes of this block from the embedded subsystem
        setup_output_datatype_inheritance( 
            normal_outputs_of_embedding_block=self.normal_outouts, 
            subsystem_prototype=self._subsystem_wrapper 
        )

        self.outputs_map_from_embedding_block_to_subsystem = OutputMapEmbeddingBlockToSubsystem( 
            normal_outputs_of_embedding_block=self.normal_outouts, 
            subsystem_prototype=self._subsystem_wrapper 
        )


        # build a list of control signals (TODO: add to MultiSubsystemEmbedder)
        self._control_signals_from_embedded_system = []
        
        # iterate over the control outputs of the embedded subsystem
        for i in range(self.number_of_normal_outputs, self.number_of_normal_outputs + self.number_of_control_outputs ):
            self._control_signals_from_embedded_system.append( self._subsystem_wrapper.outputs[i] )


    # unused / reserved for future use
    @property
    def control_outputs(self):
        return self.outputs[ self.number_of_normal_outputs: ]

    @property
    def normal_outouts(self):
        return self.outputs[ 0:self.number_of_normal_outputs ]

        
    def compile_callback_all_subsystems_compiled(self):

        # call back of the embedding of the subsystem
        self._subsystem_wrapper.callback_on_system_compiled( self.getUniqueVarnamePrefix() )

        # Get all input signals required by the subsystem
        set_of_all_inputs = set()
        set_of_all_inputs.update( self._subsystem_wrapper.inputs )

        # add the control inputs
        set_of_all_inputs.update( self._control_inputs )

        self._list_of_all_inputs = list(set_of_all_inputs)

        # determine inputs needed directly to compute the outputs

 

    def compile_callback_all_datatypes_defined(self):
        pass


    def config_request_define_feedforward_input_dependencies(self, outputSignal):

        # NOTE: This is a simplified variant so far..
        #       Every output depends on every signal
        #
        # lookup better information about feedthrough inside the manifest of the embedded subsystem

        return self._list_of_all_inputs
        

    def config_request_define_state_update_input_dependencies(self, outputSignal):
 
        # NOTE: This is a simplified variant so far..
        #       The update depends on every signal

        return self._list_of_all_inputs



    def generate_code_defStates(self, language):
        if language == 'c++':

            lines = ''
            lines += self._subsystem_wrapper.generate_code_defStates(language)

            return lines


    def generate_code_reset(self, language):
        if language == 'c++':


            lines = '// reset state of subsystem embedded by ' + self.name + '\n'
            lines += self._subsystem_wrapper.generate_code_reset(language)

            return lines
