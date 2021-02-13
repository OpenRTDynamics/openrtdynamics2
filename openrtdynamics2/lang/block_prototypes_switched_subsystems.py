from .diagram_core.system import System
from .diagram_core import datatypes as dt
from .diagram_core.signal_network.signals import Signal
from .diagram_core import code_generation_helper as cgh
from . import block_interface as bi
from .block_prototypes_subsystems import *



class MultiSubsystemEmbedder(bi.BlockPrototype):
    """
        Prototype for a block that includes multiple sub-systems whose outputs are joint in a switching manner
          (this is class to be derived, e.g. by StatemachineSwichSubsystems, SwichSubsystems)

        - control_inputs                        - inputs used to control the switching strategy
        - subsystem_prototypes                  - a list of the prototypes of all subsystems (of type GenericSubsystem)
        - switch_reference_outputs              - output signals of the reference subsystem from which the output datatypes are inherited
        - number_of_control_outputs             - the number of outputs of the subsystems used to control the execution

        - helper function for code generation -

        - self.generate_switch(), generate_reset()
    """
    def __init__(self, sim : System, control_inputs : List [Signal], subsystem_prototypes : List [GenericSubsystem], switch_reference_outputs : List [Signal], number_of_control_outputs : int = 0 ):

        assert number_of_control_outputs >= 0

        # a list of the prototypes of all subsystems
        self._subsystem_prototypes = subsystem_prototypes
        
        # analyze the default subsystem (the first) to get the output datatypes to use
        reference_subsystem_prototype = self._subsystem_prototypes[0] # [0] DIFF

        # the number of outputs besides the subsystems outputs
        self._number_of_control_outputs = number_of_control_outputs

        self._total_number_of_subsystem_outputs = len(reference_subsystem_prototype.outputs)
        self._number_of_switched_outputs = len(switch_reference_outputs)  # DIFF:  self._number_of_normal_outputs

        if self._number_of_switched_outputs + number_of_control_outputs != self._total_number_of_subsystem_outputs:
            raise BaseException("given number of total subsystem outputs does not match")

        self._number_of_outputs_of_all_nested_systems = len(reference_subsystem_prototype.outputs)

        # assertion
        for subsystem_prototype in self._subsystem_prototypes:
            if not len(subsystem_prototype.outputs) == self._total_number_of_subsystem_outputs:
                raise BaseException("all subsystems must have the same number of outputs")


        # now call the constructor for block prototypes and make input and output signals available
        bi.BlockPrototype.__init__(self, sim=sim, inputSignals=None, N_outputs = self._total_number_of_subsystem_outputs )



        # control inputs that are used to control how the subsystems are handled
        self._control_inputs = control_inputs 

        # a list of all inputs used by all subsystems
        self._list_of_all_subsystem_inputs = None

        # a list of all inputs including self._list_of_all_subsystem_inputs and self._control_inputs
        # will be filled in on compile_callback_all_subsystems_compiled()
        self._list_of_all_inputs = None





        # inherit output datatypes of this block from the embedded subsystem
        setup_output_datatype_inheritance( 
            normal_outputs_of_embedding_block=self.subsystem_switch_outouts, 
            subsystem_prototype=reference_subsystem_prototype
        )

        # build the mapping between the signals of the embedding block and the (reference) embedded block
        # please note that this consideres normal ouputs and control outputs combined.
        self.outputs_map_from_embedding_block_to_subsystem = OutputMapEmbeddingBlockToSubsystem( 
            normal_outputs_of_embedding_block=self.outputs, 
            subsystem_prototype=reference_subsystem_prototype 
        )


    @property
    def additional_outputs(self):
        return self.outputs[ self._number_of_switched_outputs: ]

    @property # rename to normal_outputs
    def subsystem_switch_outouts(self):
        return self.outputs[ 0:self._number_of_switched_outputs ]


    def compile_callback_all_subsystems_compiled(self):

        # Get all input signals required by the subsystems and avoid duplicates. 
        # Go through each subsystem in self._subsystem_prototypes and collect all input signals
        # in a set.
        set_of_all_inputs = set()

        for subsystem_prototype in self._subsystem_prototypes:
            set_of_all_inputs.update( subsystem_prototype.inputs )

        self._list_of_all_subsystem_inputs = list( set_of_all_inputs )

        # add additional inputs
        set_of_all_inputs.update( self._control_inputs )

        self._list_of_all_inputs = list(set_of_all_inputs)
            


    def compile_callback_all_datatypes_defined(self):
        pass



    def config_request_define_feedforward_input_dependencies(self, outputSignal):

        # NOTE: This is a simplified veriant so far..
        #       Every output depends on every signal

        return self._list_of_all_inputs
        

    def config_request_define_state_update_input_dependencies(self, outputSignal):
 
        # NOTE: This is a simplified veriant so far..
        #       The update depends on every signal

        return self._list_of_all_inputs



    # for code_gen
    def generate_switch( self, language, switch_control_signal_name, switch_ouput_signals=None, calculate_outputs = True, update_states = False, additional_outputs=None ):
        """
            code generation helper to embed multiple subsystems and a switch for the outputs
        """

        if calculate_outputs:
            # combine all output names to one list: normal subsystem outputs and control outputs
            assign_to_signals = []
            assign_to_signals.extend( switch_ouput_signals )
            if additional_outputs is not None:
                assign_to_signals.extend( additional_outputs )

            #
            indices_of_outputs_to_compute = self.outputs_map_from_embedding_block_to_subsystem.map_to_output_index( assign_to_signals )

        # code gen
        lines = ''

        action_list = []
        condition_list = []

        subsystem_counter = 0
        for system_prototype in self._subsystem_prototypes:

            if calculate_outputs:

                # Ah well.. this is supposed to do: system_prototype.outputs[  indices_of_outputs_to_compute  ]
                tmp = []
                for i in indices_of_outputs_to_compute:
                    tmp.append( system_prototype.outputs[i] )

                # generate code to call subsystem output(s)
                code_compute_output = embed_subsystem3(
                    language, 
                    subsystem_prototype=system_prototype, 
                    assign_to_signals=assign_to_signals, 
                    ouput_signals_of_subsystem = tmp,
                    calculate_outputs = True, update_states = False 
                )

            else:
                code_compute_output = '' # no operation


            if update_states:
                code_compute_state_update = embed_subsystem3(
                    language, 
                    subsystem_prototype=system_prototype, 
                    calculate_outputs = False, update_states = True
                )
            else:
                code_compute_state_update = '' # no operation

            action_list.append( code_compute_output + code_compute_state_update )

            # generate conditions when to execute the respective subsystem 
            condition_list.append( cgh.generate_compare_equality_to_constant( language, switch_control_signal_name , subsystem_counter ) )

            subsystem_counter += 1

        # combine conditions and their repective actions
        lines += cgh.generate_if_else(language, condition_list, action_list)

        return lines


    
    def generate_code_defStates(self, language):
        if language == 'c++':

            # implement state definition for each subsystem
            lines = ''
            for system_prototype in self._subsystem_prototypes:
                lines += system_prototype.generate_code_defStates(language)

            return lines

    def generate_reset(self, language, system_index):
        """
            helper fn for code generation
        """

        system_to_reset = self._subsystem_prototypes[ system_index ]

        lines = system_to_reset.generate_code_reset(language)

        return lines

    def generate_code_reset(self, language):
        if language == 'c++':

            # reset all subsystems
            lines = '// reset state of all subsystems in multisubsystem ' + self.name + '\n'
            for system_prototype in self._subsystem_prototypes:
                lines += system_prototype.generate_code_reset(language)

            return lines
