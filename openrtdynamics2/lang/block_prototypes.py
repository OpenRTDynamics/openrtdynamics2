from .libdyn import Simulation
from . import datatypes as dt

from .system_context import get_simulation_context
from . import block_interface as bi
from .signal_interface import *
from . import code_generation_helper as cgh

# TODO: rename to atomic_blocks

#
# Subsystem prototypes
#

class GenericSubsystem(bi.BlockPrototype):
    """
        Include a sub-system by passing a manifest

        - sim - the simulation this block is embedded into

        parameters required only in case the subsystem is already defined (e.g. loaded from a library):

        - manifest           - the manifest of the subsystem to include (optional, might be handed over by init())
        - inputSignals       - the inputs to the subsystem 
        - N_outputs          - prepare a number of nOutputs (optional in case a manifest is given)
        - embedded_subsystem - the system to embed (optional in case a manifest to an already compiled subsystem is given, NOT IMPLEMENTED)

        Note: the number of outputs must be defined either by N_outputs or by a manifest

    """
    def __init__(self, sim : Simulation = None, manifest=None, inputSignals=None, N_outputs = None, embedded_subsystem=None ):

        self.manifest = manifest
        self.inputSignals = inputSignals
        self.sim = sim
        self.Noutputs = N_outputs
        self._embedded_subsystem = embedded_subsystem

        if manifest is not None:
            if N_outputs is None:
                self.Noutputs = self.manifest.number_of_default_ouputs
            else:
                raise BaseException("N_outputs and a manifest specified at the same time")

        # output signals that were created by sth. ourside of this prototype
        # and that need to be connected to the actual outputs when init() is called.
        self.anonymous_output_signals = None

        # optional (in case this block is in charge of putting the code for the subsystem)
        self.compileResult = None

        # init super class
        bi.BlockPrototype.__init__(self, self.sim, N_outputs = self.Noutputs)

        # Note: the inputSignals are not defined when subsystems are pre-defined in the code
        # but are automatically placed and connected by the compiler during compilation

        # check if it is already possible to init this prototype
        # (in case all requred information is available)
        if inputSignals is not None and manifest is not None:
            self.init()

        # configure datatype inheritance for the outputs signals
        for i in range(0, len( embedded_subsystem.primary_outputs )):

            output_signal_of_embedding_block = self.outputs[i]
            output_signal_of_subsystem = embedded_subsystem.primary_outputs[i]

            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )

    @property
    def embedded_subsystem(self):
        """
            Return the system that is embedded (in case it was provided, returns None otherwise)
        """

        return self._embedded_subsystem

    def set_anonymous_output_signal_to_connect(self, anonymous_output_signals):
        """
            store a list of anonymous signals to connect to the outputs of the subsystems
            after running the post_compile_callback
        """
        # List of raw signals 
        self.anonymous_output_signals = anonymous_output_signals

    def compile_callback_all_subsystems_compiled(self):

        embedded_system = self._embedded_subsystem
        #
        # continue init as now all subsystems are compiled and the compile results and the manifest of
        # the system to compile is available.
        #
        self.init(embedded_system.compilationResult.manifest, embedded_system.compilationResult, embedded_system.compilationResult.inputSignals)

    # post_compile_callback (called after the subsystem to embedd was compiled)
    def init(self, manifest, compileResult, inputSignals):
        """
            This is a second phase initialization of this subsystem block 
            (to be called by compile_callback_all_subsystems_compiled())

            This function shall be called when the subsystem to embedd is compiled
            after the instance of 'GenericSubsystem' is created. This way, it is possible
            to add blocks embeddeding sub-systems without haveing these subsystems to be
            already compiled.

            Optionally, the system this block belongs to can be set.

            manifest       - the system manifest of the subsystem to embedd
            compileResults - the compile results of the subsystem to embedd
            inputSignals   - input signals to the subsystem to embedd (links comming from an upper-level subsystem)

        """        

        #
        #    set the manifest of the subsystem
        #
        if self.manifest is not None:
            raise BaseException("cannot call this function as the subsystem's manifest was already defined in the constructor.")

        self.manifest = manifest

        #
        #    Set the compilation result of the embedded system (if available)
        #
        self.compileResult = compileResult

        #
        #    connect the inputs (coming from the upper-level system)
        #

        if self.inputSignals is not None:
            raise BaseException("The subsystem's inputSignals were already specified in the constructor.")

        self.inputSignals = inputSignals



        def collectDependingSignals(signals, manifestFunctionInputs):
            # collect all depending input signals (that are needed to calculate the output) in a list
            # MOVE TO A FUNCTION. MAYBE MOVE TO MANIFEST.PY
            dependingInputs = []
            for i in range( len(manifestFunctionInputs['names']) ):

                dependingInput_name = manifestFunctionInputs['names'][i]
                dependingInput_type = manifestFunctionInputs['types'][i]
                dependingInput_cpptype = manifestFunctionInputs['cpptypes'][i]

                # TODO: CHECK FOR FAILING LOOKUP
                signal = signals[ dependingInput_name ]

                # check datatype
                if not signal.getDatatype().cppDataType == dependingInput_cpptype:
                    raise BaseException('datatype does not match the one specified in the manifest. (' + (dependingInput_cpptype) + ' is required in the manifest)' )

                # append signal
                dependingInputs.append( signal ) 

            return dependingInputs



        # verify the number of outputs of the embedded system
        number_of_outputs_as_described_by_manifest = self.manifest.number_of_default_ouputs

        if not number_of_outputs_as_described_by_manifest == self.Noutputs:
            BaseException("missmatch in the number of outputs")

        # get the output datatypes of the embedded system
        self.outputTypes = self.manifest.io_outputs['calculate_output']['types']  


        if self.compileResult is None:
            # collect all depending input signals (that are needed to calculate the output) in a list
            self.inputsToCalculateOutputs = collectDependingSignals( self.inputSignals, self.manifest.io_inputs['calculate_output'] )

            # collect all inputs required to perform the state update
            self.inputsToUpdateStates = collectDependingSignals( self.inputSignals, self.manifest.io_inputs['state_update'] )

        else:
            # use the available compile results to get the I/O signals
            # in this case, self.inputSignals shall be a list of signals. The order
            # shall match the signal order in self.compileResults.inputSignals

            self.inputsToCalculateOutputs = self.compileResult.simulationInputSignalsToCalculateOutputs
            self.inputsToUpdateStates = self.compileResult.simulationInputSignalsToUpdateStates

            

        # combine all inputs to a list
        self.allInputs = list()

        self.allInputs.extend( self.inputsToCalculateOutputs )
        self.allInputs.extend( self.inputsToUpdateStates )

        #
        # now initialize the propotype
        #

        # define the inputs
        self.update_input_config( self.allInputs )

        # connect the outputs signals
        if self.anonymous_output_signals is not None:

            print(" -- Nesting block: connecting anonymous signals -- ")

            Ns = len(self.outputSignals)

            if not Ns == len(  self.anonymous_output_signals ):
                raise BaseException(" missmatch in the number of output signals")

            for i in range(0,Ns):
                
                s_ananon = self.anonymous_output_signals[i]
                s_source = self.outputSignals[i]

                print("connecting the output " + s_ananon.toStr() + " of the embedding block")
                s_ananon.setequal( s_source )



        # for code generation
        self.instanceVarname = self.getUniqueVarnamePrefix() + '_subsystem_' + self.manifest.API_name


    def config_request_define_output_types(self, inputTypes):

        # the datatypes are fixed in the manifest 
        return self.outputTypes        

    def config_request_define_feedforward_input_dependencies(self, outputSignal):

        # NOTE: This is a simplified veriant so far.. no dependence on the given 'outputSignal'
        #       (Every output depends on every signal in self.inputsToCalculateOutputs)

        # TODO: 6.10.19 implement this in a more granular way.
        # also use self.compileResults to get those information

        return self.inputsToCalculateOutputs

    def config_request_define_state_update_input_dependencies(self, outputSignal):
 
        # return a list of input signals that are required to update the states
        return self.inputsToUpdateStates



    def codegen_addToNamespace(self, language):
        lines = ''

        # putting code for subsystems is performed using execution commands

        return lines

    def generate_code_defStates(self, language):
        if language == 'c++':
            lines = '// instance of ' + self.manifest.API_name + '\n'
            lines += self.manifest.API_name + ' ' + self.instanceVarname + ';\n'

            return lines

    def generate_code_reset(self, language):
        if language == 'c++':
            return self.instanceVarname + '.' + self.manifest.getAPIFunctionName('reset') +  '();\n'


    def generate_code_init(self, language):
        pass


    def generate_code_destruct(self, language):
        pass


    # helper fn to build code
    def generate_code_call_OutputFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('calculate_output') +  '(' + cgh.signal_list_to_names_string(self.outputs + self.inputsToCalculateOutputs) + ');\n'

    # helper fn to build code
    def generate_code_call_UpdateFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('state_update') +  '(' + cgh.signal_list_to_names_string(self.inputsToUpdateStates) + ');\n'

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = ''
            
            #
            # TODO: 2.5.2020: concept: how to compute only the nescessary signals?
            #

            for s in self.outputs:
                lines += cgh.define_variable_line( s ) 

                if s not in signals:
                    lines += '// NOTE: unused output signal' + s.name + '\n'
                else:
                    lines += ''                

            lines += self.generate_code_call_OutputFunction(self.instanceVarname, self.manifest, language)

        return lines

    def generate_code_update(self, language):
        if language == 'c++':

            # input to this call are the signals in self.inputsToUpdateStates
            return self.generate_code_call_UpdateFunction(self.instanceVarname, self.manifest, language)

def generic_subsystem( manifest, inputSignals : List[SignalUserTemplate] ):
    return wrap_signal_list( GenericSubsystem(get_simulation_context(), manifest, unwrap_hash(inputSignals) ).outputSignals )



















class SingleSubsystemEmbedder(bi.BlockPrototype):
    """
        Prototype for a block that includes one sub-system
          (this is class to be derived, e.g. by XX, XX)

        - control_inputs                        - inputs used to control the execution (e.g. the condition for if)
        - subsystem_prototype                   - the prototypes the subsystem (of type GenericSubsystem)
        - reference_outputs                     - output signals of the reference subsystem from which the output datatypes are inherited
        - number_of_control_outputs             - the number of outputs of the subsystem used to control execution

        - helper function for code generation -

        - XX

                         
                        +--------------------------------------------------+
                        | SingleSubsystemEmbedder                          |
                        |                       +-------------+            |
        normal input 1  |                       |             |            |  normal output 1
                     +------------------------->+             +--------------->
                        |                       |   embeded   |            |
        normal input 2  |                       |             |            |  normal output 2
                     +------------------------->+             +--------------->
                        |                       |  subsystem  |            |
                        |        control status |             | control    |
                        |            +--------->+             +-----+      |
                        |            |          |             | output     |
                        |            |          +-------------+     |      |
                        |            |                              |      |
                        |     +------+------+                       |      |
        control input   |     |  execution  |                       |      |
                     +------->+  control of +<----------------------+      |
                        |     |  subsystem  |                              |
                        |     +-------------+                              |
                        |                                                  |
                        +--------------------------------------------------+

        Picture drawn by http://asciiflow.com/



        lists of output signals
        -----------------------

        self.outputs                                           - all outputs of the embeding block
        self._subsystem_prototype.outputs                      - all outputs of the subsystem that are initialily present
        self._subsystem_prototype.compileResult.outputSignals  - all outputs of the subsystem that are present after compilation
        signals (parameter for generate_code_output_list)      - outputs out of self.outputs that need to be computed

    """
    def __init__(self, sim : Simulation, control_inputs : List [Signal], subsystem_prototype : GenericSubsystem, number_of_control_outputs : int = 0 ):

        # the prototypes of the subsystem
        self._subsystem_prototype = subsystem_prototype
        
        # analyze the default subsystem (the first) to get the output datatypes to use
        reference_subsystem = self._subsystem_prototype

        # the number of outputs besides the subsystems outputs
        self._number_of_control_outputs = number_of_control_outputs

        self._total_number_of_subsystem_outputs = len(reference_subsystem.outputs)
        self._number_of_normal_outputs = len(self._subsystem_prototype.outputs) - number_of_control_outputs

        if self._number_of_normal_outputs < 0:
            raise BaseException("The number of control outputs is higher than the toal number of outputs provided by the subsystem.")

        self._number_of_outputs_of_all_nested_systems = len(reference_subsystem.outputs)



        # now call the constructor for block prototypes and make input and output signals available
        bi.BlockPrototype.__init__(self, sim=sim, inputSignals=None, N_outputs = self._number_of_normal_outputs )



        # control inputs that are used to control how the subsystems are handled
        self._control_inputs = control_inputs 


        # a list of all inputs including self._list_of_all_subsystem_inputs and self._control_inputs
        # will be filled in on compile_callback_all_subsystems_compiled()
        self._list_of_all_inputs = None


        # output sigal mapping: map each output of SingleSubsystemEmbedder to an output of the subsystem
        self._output_signal_mapping = {} # (TODO: extend/add to MultiSubsystemEmbedder)

        # inherit output datatypes of this block from the embeded subsystem
        for i in range(0, self._number_of_normal_outputs ):

            # fill in mapping table
            self._output_signal_mapping[ self.outputs[i] ] = self._subsystem_prototype.outputs[i]

            output_signal_of_embedding_block = self.outputs[i]
            output_signal_of_subsystem = self._subsystem_prototype.outputs[i] # reference_outputs[i]
            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )

            #output_signal_of_embedding_block.set_data_link( output_signal_of_subsystem )

        # build a list of control signals (TODO: add to MultiSubsystemEmbedder)
        self._control_signals_from_embeded_system = []
        
        # iterate over the control outputs of the embedded subsystem
        for i in range(self._number_of_normal_outputs, self._number_of_normal_outputs + self._number_of_control_outputs ):
            self._control_signals_from_embeded_system.append( self._subsystem_prototype.outputs[i] )


    @property
    def additional_outputs(self):
        return self.outputs[ self._number_of_normal_outputs: ]

    @property
    def normal_outouts(self):
        return self.outputs[ 0:self._number_of_normal_outputs ]


    def compile_callback_all_subsystems_compiled(self):

        # Get all input signals required by the subsystem
        set_of_all_inputs = set()
        set_of_all_inputs.update( self._subsystem_prototype.inputs )

        # add the control inputs
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


    def helper_get_output_signal_mapping_to_subsystem(self, signals_to_calculate):

        mapped_subsystem_output_signals = []
        for s in signals_to_calculate:
            mapped_subsystem_output_signals.append( self._output_signal_mapping[s] )

        return mapped_subsystem_output_signals
    
    def generate_code_defStates(self, language):
        if language == 'c++':

            lines = ''
            lines += self._subsystem_prototype.generate_code_defStates(language)

            return lines


    def generate_code_reset(self, language):
        if language == 'c++':


            lines = '// reset state of subsystem embeded by ' + self.name + '\n'
            lines += self._subsystem_prototype.generate_code_reset(language)

            return lines










class TruggeredSubsystem(SingleSubsystemEmbedder):
    """
        Include a triggered sub-system

        Optional:

            prevent_output_computation = True: 
                The subsystems outputs are only computed when triggered. Please note that the outputs
                of the subsystem are uninitialized until the subsystem is triggered for the first time.

    """


    def __init__(self, sim : Simulation, control_input : Signal, subsystem_prototype : GenericSubsystem,  prevent_output_computation = False ):
        
        self._control_input = control_input
        self.prevent_output_computation = prevent_output_computation

        SingleSubsystemEmbedder.__init__(self, sim, 
                                        control_inputs=[control_input], 
                                        subsystem_prototype=subsystem_prototype, 
                                        number_of_control_outputs=0 )



    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':
            
            # code_compute_output = self._subsystem_prototype.generate_code_output_list(language, self._subsystem_prototype.outputs)




            code_compute_output = cgh.embed_subsystem(language, system_prototype=self._subsystem_prototype, ouput_signals_name=cgh.signal_list_to_name_list(signals), calculate_outputs = True, update_states = False )


            if self.prevent_output_computation:

                # the subsystems outputs are only computed when triggered
                lines += cgh.generate_if_else(language, 
                    condition_list=[ cgh.generate_compare_equality_to_constant( language, self._control_input, 1 ) ], 
                    action_list=[ code_compute_output ])

                # TODO: copy output signals and only the ones requested

            else:
                # the subsystems outputs are always computed
                lines += code_compute_output


        return lines

    def generate_code_update(self, language):

        lines = ''
        if language == 'c++':

            code_compute_state_update = self._subsystem_prototype.generate_code_update(language)

            # the subsystems update is on only performed when triggered
            lines += cgh.generate_if_else(language, 
                condition_list=[ cgh.generate_compare_equality_to_constant( language, self._control_input.name, 1 ) ], 
                action_list=[ code_compute_state_update ])

        return lines






class LoopUntilSubsystem(SingleSubsystemEmbedder):
    """
        Embed a loop sub-system

    """

    def __init__(self, sim : Simulation, max_iteriations : int, 
                    subsystem_prototype : GenericSubsystem, 
                    until_signal : Signal = None, yield_signal : Signal = None ):
        
        self.max_iter = max_iteriations
        self._until_signal = until_signal
        self._yield_signal = yield_signal

        number_of_control_outputs = 0
        if self._until_signal is not None:
            number_of_control_outputs += 1

        if self._yield_signal is not None:
            number_of_control_outputs += 1


        SingleSubsystemEmbedder.__init__(self, sim, 
                                        control_inputs=[],   # TODO: add N_iter signal here 
                                        subsystem_prototype=subsystem_prototype, 
                                        number_of_control_outputs=number_of_control_outputs )


    # def config_request_define_state_update_input_dependencies(self, outputSignal):
 
    #     return [self._until_signal]

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':

            # output signal mapping lookup
            ouput_signals_of_subsystem = self.helper_get_output_signal_mapping_to_subsystem(signals_to_calculate=signals)


            ouput_signals_names = cgh.signal_list_to_name_list(signals)
            ouput_signal_names_of_subsystem = cgh.signal_list_to_name_list(ouput_signals_of_subsystem)
            

            loop_break_condition = []

            control_output_index = 0

            if self._until_signal is not None:
                # define tmp-var for self._until_signal instead of a block output
                lines += cgh.defineVariables( [self._until_signal] )

                # add list of signals to assign
                ouput_signals_names.append( self._until_signal.name )
                ouput_signal_names_of_subsystem.append( self._control_signals_from_embeded_system[control_output_index].name )
            
                # add break condition
                loop_break_condition.append( self._until_signal.name )

                control_output_index += 1


            if self._yield_signal is not None:
                # define tmp-var for self._yield_signal instead of a block output
                lines += cgh.defineVariables( [self._yield_signal] )

                # add list of signals to assign
                ouput_signals_names.append( self._yield_signal.name )
                ouput_signal_names_of_subsystem.append( self._control_signals_from_embeded_system[control_output_index].name )

                # add break condition
                loop_break_condition.append( self._yield_signal.name )

                control_output_index += 1


            calc_outputs = cgh.embed_subsystem2(language, 
                        system_prototype=self._subsystem_prototype, 
                        ouput_signals_name=ouput_signals_names, 
                        ouput_signal_names_of_subsystem=ouput_signal_names_of_subsystem,
                        calculate_outputs = True, update_states = False )

            update_states = cgh.embed_subsystem2(language, 
                        system_prototype=self._subsystem_prototype, 
                        calculate_outputs = False, update_states = True )

            code = ''
            code +=  calc_outputs 
            code += update_states

            if self._yield_signal is not None:
                code += cgh.generate_loop_break(language, condition=self._yield_signal.name)

            if self._until_signal is not None:
                code_reset_subsystem = self._subsystem_prototype.generate_code_reset(language)
                code += cgh.generate_loop_break(language, condition=self._until_signal.name, code_before_break=code_reset_subsystem)

            lines += cgh.generate_loop( language, max_iterations=str(self.max_iter), code_to_exec=code  )

        return lines

    def generate_code_update(self, language):

        lines = ''
        if language == 'c++':

            if self._until_signal is not None:
                pass    
                #lines += self._subsystem_prototype.generate_code_reset(language)


        return lines























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
    def __init__(self, sim : Simulation, control_inputs : List [Signal], subsystem_prototypes : List [GenericSubsystem], switch_reference_outputs : List [Signal], number_of_control_outputs : int = 0 ):

        # a list of the prototypes of all subsystems
        self._subsystem_prototypes = subsystem_prototypes
        
        # analyze the default subsystem (the first) to get the output datatypes to use
        reference_subsystem = self._subsystem_prototypes[0]

        # the number of outputs besides the subsystems outputs
        self._number_of_control_outputs = number_of_control_outputs

        self._total_number_of_subsystem_outputs = len(reference_subsystem.outputs)
        self._number_of_switched_outputs = len(switch_reference_outputs)

        if self._number_of_switched_outputs + number_of_control_outputs != self._total_number_of_subsystem_outputs:
            raise BaseException("given number of total subsystem outputs does not match")

        self._number_of_outputs_of_all_nested_systems = len(reference_subsystem.outputs)

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

        # inherit output datatypes of the reference subsystem
        for i in range(0, self._number_of_switched_outputs ):

            output_signal_of_embedding_block = self.outputs[i]
            output_signal_of_subsystem = switch_reference_outputs[i]
            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )

        # NOTE: datatypes for control outputs are untouched

    @property
    def additional_outputs(self):
        return self.outputs[ self._number_of_switched_outputs: ]

    @property
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
    def generate_switch( self, language, switch_control_signal_name, switch_ouput_signals_name=None, calculate_outputs = True, update_states = False, additional_outputs_names=None ):
        """
            code generation helper to embed multiple subsystems and a switch for the outputs
        """

        lines = ''

        action_list = []
        condition_list = []

        subsystem_counter = 0
        for system_prototype in self._subsystem_prototypes:

            if calculate_outputs:
                # combine all output names to one list: normal subsystem outputs and control outputs
                ouput_signals_name = []
                ouput_signals_name.extend( switch_ouput_signals_name )
                ouput_signals_name.extend( additional_outputs_names )

                # call each subsystem embedder to generate its code
                code_calculate_outputs = cgh.embed_subsystem( language, system_prototype, ouput_signals_name=ouput_signals_name)
            else:
                code_calculate_outputs = '' # no operation


            if update_states:
                # call each subsystem embedder to generate its update code
                code_update_states = cgh.embed_subsystem( language, system_prototype, calculate_outputs=False, update_states=True)
            else:
                code_update_states = '' # no operation

            action_list.append( code_calculate_outputs + code_update_states )

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



class SwichSubsystems(MultiSubsystemEmbedder):
    """
        A system that includes multiple subsystems and a control input to switch in-between
        The outputs of the currently acrive subsystem are forwarded.
    """

    def __init__(self, sim : Simulation, control_input : Signal, subsystem_prototypes : List [GenericSubsystem], reference_outputs : List [Signal] ):
        
        self._control_input = control_input

        MultiSubsystemEmbedder.__init__(self, sim, 
                                        control_inputs=[control_input], 
                                        subsystem_prototypes=subsystem_prototypes, 
                                        switch_reference_outputs=reference_outputs,
                                        number_of_control_outputs=0 )


    def generate_code_defStates(self, language):
        lines = MultiSubsystemEmbedder.generate_code_defStates(self, language)
        lines += '' # add something
        
        return lines


    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':
            
            # the method self.generate_switch is provided by MultiSubsystemEmbedder 
            lines += self.generate_switch( language=language, 
                                            switch_control_signal_name=self._control_input.name,
                                            switch_ouput_signals_name= cgh.signal_list_to_name_list(signals),
                                             calculate_outputs = True, update_states = False )

        return lines

    def generate_code_update(self, language):

        lines = ''
        if language == 'c++':
            lines += self.generate_switch( language=language, 
                                                    switch_control_signal_name=self._control_input.name,
                                                     calculate_outputs = False, update_states = True )

        return lines







class StatemachineSwichSubsystems(MultiSubsystemEmbedder):
    """

    """

    def __init__(self, sim : Simulation, subsystem_prototypes : List [GenericSubsystem], reference_outputs : List [Signal] ):
        
        MultiSubsystemEmbedder.__init__(self, sim, 
                                        control_inputs=[], 
                                        subsystem_prototypes=subsystem_prototypes, 
                                        switch_reference_outputs=reference_outputs,
                                        number_of_control_outputs = 1 )

        # how to add more outputs?
        self.state_output.setDatatype( dt.DataTypeInt32(1) )

        # this output signals must be compted in any way
        # also in case it is not used by other blocks
        sim.add_signal_mandatory_to_compute( self.state_output )


    @property
    def state_output(self):
        return self.additional_outputs[0]


    def generate_code_reset(self, language):
        if language == 'c++':

            lines = self._state_memory + ' = 0;\n' # add something

            lines += MultiSubsystemEmbedder.generate_code_reset(self, language)

            return lines


    def generate_code_defStates(self, language):
        lines = MultiSubsystemEmbedder.generate_code_defStates(self, language)

        self._state_memory = self.getUniqueVarnamePrefix() + 'state'
        lines += 'int ' + self._state_memory + ' {0};'
        
        return lines


    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':

            # do not compute all swich outputs, just the ones requested by 'signals' 
            outputs_to_compute = []
            for s in signals:
                if s in self.subsystem_switch_outouts:
                    outputs_to_compute.append( s )


            # lines += cgh.defineVariables( signals ) + '\n'
            lines += self.generate_switch( language=language, 
                                            switch_control_signal_name=  self._state_memory ,
                                            switch_ouput_signals_name=cgh.signal_list_to_name_list(outputs_to_compute),
                                            additional_outputs_names=[self.state_output.name] )

            # lines += self.state_output.name + ' = ' + self._state_memory_delayed + ';\n'

        return lines


    # code_gen helper
    def generate_switch_to_reset_leaving_subsystem( self, language, switch_control_signal_name ):

        lines = ''

        action_list = []
        condition_list = []

        subsystem_counter = 0
        for system_prototype in self._subsystem_prototypes:

            code_reset_states = MultiSubsystemEmbedder.generate_reset( self, language, system_index=subsystem_counter ) 

            action_list.append(  code_reset_states )

            # generate conditions when to execute the respective subsystem 
            condition_list.append( cgh.generate_compare_equality_to_constant( language, switch_control_signal_name , subsystem_counter ) )

            subsystem_counter += 1

        # combine conditions and their repective actions
        lines += cgh.generate_if_else(language, condition_list, action_list)

        return lines

    def generate_code_update(self, language):

        lines = ''
        if language == 'c++':
            lines += self.generate_switch( language=language, 
                                                    switch_control_signal_name=self._state_memory,
                                                    calculate_outputs=False, 
                                                    update_states=True )


            # get the signal issued by the currently active subsystem that describes state chanhe requests
            state_control_signal_from_subsystems = self.state_output

            # reset current subsystem in case a state transition is requested
            lines_reset_subsystem = self.generate_switch_to_reset_leaving_subsystem(language, self._state_memory )
            lines += cgh.generate_if_else(language, condition_list=[ state_control_signal_from_subsystems.name + ' >= 0 ' ], action_list=[lines_reset_subsystem])

            # transition to the new state
            lines += self._state_memory + ' = (' + state_control_signal_from_subsystems.name + ' >= 0 ) ? ('+ state_control_signal_from_subsystems.name + ') : (' + self._state_memory + ');\n'
            
        return lines













#
# Sources
#

class Const(bi.StaticSource_To1):
    def __init__(self, sim : Simulation, constant, datatype ):

        self.constant = constant

        # call super
        bi.StaticSource_To1.__init__(self, sim, datatype)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str( self.constant ) + ';\n'

def const(constant, datatype ):
    return wrap_signal( Const(get_simulation_context(), constant, datatype).outputs[0] )




#
# Multiply by constant
#

class Gain(bi.StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, factor : float ):

        self._factor = factor

        bi.StaticFn_1To1.__init__(self, sim, u)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._factor) + ' * ' + self.inputs[0].name +  ';\n'

def gain(u : SignalUserTemplate, gain : float ):
    return wrap_signal( Gain(get_simulation_context(), u.unwrap, gain).outputs[0] )


#
# Cast to given datatype
#

class ConvertDatatype(bi.StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, target_type : dt.DataType ):

        self._target_type = target_type

        bi.StaticFn_1To1.__init__(self, sim, u)

    def config_request_define_output_types(self, inputTypes):
        return [ self._target_type ]  

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            # TODO: only = is used and the c++ compiler decides how to convert...
            return signals[0].name + ' = ' + self.inputs[0].name + ';\n'

def convert(u : SignalUserTemplate, target_type : dt.DataType ):
    return wrap_signal( ConvertDatatype(get_simulation_context(), u.unwrap, target_type).outputs[0] )



#
# Basic operators
#

class Add(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], factors : List[float] ):

        # feasibility checks
        if len(inputSignals) != len(factors):
            raise("len(inp_list) must be equal to len(factors)")

        self.factors = factors
        bi.StaticFn_NTo1.__init__(self, sim, inputSignals)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(self.factors[i]) + ' * ' + s.name )
                i = i + 1

            sumline = ' + '.join( strs )
            lines = signals[0].name + ' = ' + sumline + ';\n'

            return lines


def add(inputSignals : List[SignalUserTemplate], factors : List[float]):
    return wrap_signal( Add(get_simulation_context(), unwrap_list( inputSignals ), factors).outputs[0] )


class Operator1(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], operator : str ):

        self.operator = operator
        bi.StaticFn_NTo1.__init__(self, sim, inputSignals)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(  s.name ) )
                i = i + 1

            sumline = (' ' + self.operator + ' ').join( strs )
            lines = signals[0].name + ' = ' + sumline + ';\n'

            return lines


def operator1(inputSignals : List[SignalUserTemplate], operator : str ):
    return wrap_signal( Operator1(get_simulation_context(), unwrap_list( inputSignals ), operator).outputs[0] )


#
# logic operators
#

def logic_and(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        logical and

        u1 && u2
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list([u1,u2]), operator=' && ').outputs[0] )

def logic_or(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        logical or
    
        u1 || u2
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list( [u1,u2] ), operator=' || ').outputs[0] )


def logic_xor(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        exclusive logical or (xor)
    
        u1 ^ u2
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list( [u1,u2] ), operator=' ^ ').outputs[0] )


def bitwise_and(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        bitwise and

        u1 & u2
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list([u1,u2]), operator=' & ').outputs[0] )

def bitwise_or(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        bitwise or
    
        u1 | u2
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list( [u1,u2] ), operator=' | ').outputs[0] )


def bitwise_shift_left(u : SignalUserTemplate, shift : SignalUserTemplate):
    """
        logical shift left
    
        u << shift
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list( [u,shift] ), operator=' << ').outputs[0] )


def bitwise_shift_right(u : SignalUserTemplate, shift : SignalUserTemplate):
    """
        logical shift left
    
        u >> shift
    """

    return wrap_signal( Operator1(get_simulation_context(), inputSignals=unwrap_list( [u,shift] ), operator=' >> ').outputs[0] )






















class ComparisionOperator(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, left : Signal, right : Signal, operator : str ):

        self.operator = operator

        bi.StaticFn_NTo1.__init__(self, sim, inputSignals = [left, right])

    def config_request_define_output_types(self, inputTypes):

        # return a proposal for an output type. 
        return [ dt.DataTypeBoolean(1) ]

    # def generate_code_output(self, language, signal : Signal):
    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = signals[0].name + ' = ' + self.inputSignals[0].name + ' ' + self.operator + ' ' + self.inputSignals[1].name + ';\n'
            return lines


def comparison(left : SignalUserTemplate, right : SignalUserTemplate, operator : str ):
    return wrap_signal( ComparisionOperator(get_simulation_context(), left.unwrap, right.unwrap, operator).outputs[0] )














class SwitchNto1(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, state : Signal, inputs : List [Signal] ):

        self.inputs = inputs
        self.state = state

        inputSignals = [state]
        inputSignals.extend(inputs)

        bi.StaticFn_NTo1.__init__(self, sim, inputSignals )

    def config_request_define_output_types(self, inputTypes):

        # check weather the trigger input is int32
        if inputTypes[0] is not None:
            if dt.DataTypeInt32(1).isEqualTo( inputTypes[0] ) == 0:
                raise BaseException('state input must be of type Int32')  

        # determine a guess for the output datatype
        # check if all given datatypes are equal
        autoDatatype = autoDatatype_Nto1(self.outputs[0].getDatatype(), inputTypes[1:-1] )

        return [ autoDatatype ]

    #def generate_code_output(self, language, signal : Signal):
    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = '\n// switch ' + str(len(self.inputs)) + ' inputs --> ' + self.state.name + '\n'
            i = 1
            for ip in self.inputs:
                if i == 1:
                    lines += 'if (' + self.state.name + ' == ' + str(i) + ') {\n'
                else:
                    lines += 'else if (' + self.state.name + ' == ' + str(i) + ') {\n'

                lines += '  ' + signals[0].name + ' = ' + ip.name + ';\n'
                lines += '} '

                i += 1

            lines += 'else {\n'
            lines += '  ' + signals[0].name + ' = ' + self.inputs[0].name + ';\n'
            lines += '}\n'
            
            return lines


def switchNto1( state : SignalUserTemplate, inputs : SignalUserTemplate ):
    return wrap_signal( SwitchNto1(get_simulation_context(), state.unwrap, unwrap_list(inputs) ).outputs[0] )




























class ConditionalOverwrite(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, signal : Signal, condition : Signal, new_value ):

        self.new_value = new_value

        if isinstance( self.new_value, Signal ): 
            bi.StaticFn_NTo1.__init__(self, sim, inputSignals = [signal, condition, new_value])
        else:
            bi.StaticFn_NTo1.__init__(self, sim, inputSignals = [signal, condition])

    def config_request_define_output_types(self, inputTypes):

        # just inherit the input type
        if isinstance( self.new_value, Signal ): 
            return [ dt.common_numeric_type( inputTypes ) ]

        else:
            return [ inputTypes[0] ]


    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':

            if isinstance( self.new_value, Signal ): 
                action_overwrite = self.outputs[0].name + ' = ' + self.inputSignals[2].name + ';'

            else:                
                action_overwrite = self.outputs[0].name + ' = ' + str( self.new_value ) + ';'

            action_keep = self.outputs[0].name + ' = ' + self.inputs[0].name + ';'

            lines = cgh.generate_if_else( language, condition_list=[ self.inputSignals[1].name ], action_list=[ action_overwrite, action_keep ] )
            return lines


def conditional_overwrite(signal : SignalUserTemplate, condition : SignalUserTemplate, new_value ):

    if isinstance(new_value, SignalUserTemplate):
        new_value = new_value.unwrap

    return wrap_signal( ConditionalOverwrite(get_simulation_context(), signal.unwrap, condition.unwrap, new_value).outputs[0] )





















#
# Static functions that map 1 --> 1
#

class StaticFnByName_1To1(bi.StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, functionName : str ):

        self._functionName = functionName

        bi.StaticFn_1To1.__init__(self, sim, u)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._functionName) + '(' + self.inputs[0].name +  ');\n'



def sqrt(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'sqrt').outputs[0] )

def sin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'sin').outputs[0] )

def cos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'cos').outputs[0] )

def tan(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'tan').outputs[0] )

def atan(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'atan').outputs[0] )

def asin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'asin').outputs[0] )

def acos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'acos').outputs[0] )

def abs(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'abs').outputs[0] )




class Operator0(bi.StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, operator_str : str ):

        self._operator_str = operator_str

        bi.StaticFn_1To1.__init__(self, sim, u)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._operator_str) + self.inputs[0].name +  ';\n'


def logic_not(u : SignalUserTemplate ):
    """
        logic negation
    """
    return wrap_signal( Operator0(get_simulation_context(), u.unwrap, '!').outputs[0] )

def bitwise_not(u : SignalUserTemplate ):
    return wrap_signal( Operator0(get_simulation_context(), u.unwrap, '~').outputs[0] )





#
# static functinos that map 2 --> 1
#

class StaticFnByName_2To1(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, left : Signal, right : Signal, function_name : str ):

        self._function_name = function_name

        bi.StaticFn_NTo1.__init__(self, sim, inputSignals = [left, right])

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = signals[0].name + ' = ' + self._function_name + '(' + self.inputSignals[0].name +  ', ' + self.inputSignals[1].name + ')' + ';\n'
            return lines


def atan2(y : SignalUserTemplate, x : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_2To1(get_simulation_context(), y.unwrap, x.unwrap, 'atan2').outputs[0] )

def pow(base : SignalUserTemplate, power : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_2To1(get_simulation_context(), base.unwrap, power.unwrap, 'pow').outputs[0] )

def fmod(x : SignalUserTemplate, y : SignalUserTemplate ):
    """
        modulo function for floating point values

        This function returns the remainder of dividing x/y.
    """
    return wrap_signal( StaticFnByName_2To1(get_simulation_context(), x.unwrap, y.unwrap, 'fmod').outputs[0] )









class GenericCppStatic(bi.BlockPrototype):
    def __init__(self, sim : Simulation, input_signals : List[Signal], input_names : List [str], input_types, output_names : List[str], output_types, cpp_source_code : str ):

        Ninputs = len(input_names)

        if not Ninputs == len(input_types):
            raise BaseException('not Ninputs == len(input_types)')

        if not Ninputs == len(input_signals):
            raise BaseException('not Ninputs == len)(input_signals)')

        if not len(output_names) == len(output_types):
            raise BaseException('not len(output_names) == len(output_types)')

        self._input_signals = input_signals
        self._input_names = input_names
        self._input_types = input_types
        self._output_names = output_names
        self._output_types = output_types
        self._cpp_source_code = cpp_source_code

        bi.BlockPrototype.__init__(self, sim, input_signals, len(output_names), output_types  )

        self._static_function_name = 'fn_static_' + str(self.id)

    def config_request_define_output_types(self, inputTypes):

        for i in range(0, len(inputTypes)):
            if inputTypes[i] is not None and not inputTypes[i].isEqualTo( self._input_types[i] ):
                raise BaseException('GenericCppStatic: datatype missmatch for input # ' + str(i) )

        # return a proposal for an output type. 
        return self._output_types

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on all inputs
        return self.inputs 

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states

    def codegen_addToNamespace(self, language):

        if language == 'c++':
            ilines = ''

            info_comment_1 = '// begin of user defined function\n'
            info_comment_2 = '\n// end of user defined function\n'

            ilines += cgh.cpp_define_function_from_types(self._static_function_name, self._input_types, self._input_names, self._output_types, self._output_names, info_comment_1 + self._cpp_source_code + info_comment_2 )

            return ilines

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':

            ilines = ''

            # create tmp output variables
            tmp_output_variable_names = []
            for i in range(0, len(self._output_names)):
                tmp_variable_name = self._static_function_name + '_' + self._output_names[i]
                tmp_output_variable_names.append( tmp_variable_name )
                ilines += self._output_types[i].cpp_define_variable(variable_name=tmp_variable_name) + ';\n'

            # function call
            ilines += cgh.call_function_from_varnames( self._static_function_name, cgh.signal_list_to_name_list(self.inputs), tmp_output_variable_names)

            # copy outputs from tmp variables
            for i in range(0, len(self._output_names)):

                # only copy the needed outputs as indicated by 'signals'
                if self.outputs[i] in signals:
                    ilines += self.outputs[i].name + ' = ' + tmp_output_variable_names[i] + ';\n'

            return '{ // calling the static function ' + self._static_function_name + '\n' + cgh.indent(ilines) + '}\n'

def generic_cpp_static(input_signals : List[SignalUserTemplate], input_names : List [str], input_types, output_types, output_names, cpp_source_code : str ):
    return wrap_signal_list( GenericCppStatic(get_simulation_context(), unwrap_list(input_signals), input_names, input_types, output_names, output_types, cpp_source_code  ).outputs )









#
# Blocks that have an internal memory
#



class Delay(bi.BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal, initial_state = None ):

        self._initial_state = initial_state
        bi.BlockPrototype.__init__(self, sim, [ u ], 1)

    def config_request_define_output_types(self, inputTypes):

        # just inherit the input type 
        output_type = inputTypes[0]

        return [ output_type ]        

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # no (direct feedtrough) dependence on any input - only state dependent
        return [  ]

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return self.inputs  # all inputs

    def generate_code_defStates(self, language):
        if language == 'c++':
            return self.outputs[0].datatype.cpp_define_variable( self.getUniqueVarnamePrefix() + '_mem' )  + ';\n'

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + self.getUniqueVarnamePrefix() + '_mem' + ';\n'

    def generate_code_update(self, language):
        if language == 'c++':

            lines = self.getUniqueVarnamePrefix() + '_mem' + ' = ' + self.inputs[0].name + ';\n'
            return lines

    def generate_code_reset(self, language):
        if language == 'c++':

            if self._initial_state is None:
                # get the zero element for the given datatype
                initial_state_str = str(self.outputs[0].datatype.cpp_zero_element)
            else:
                initial_state_str = str(self._initial_state)

            return self.getUniqueVarnamePrefix() + '_mem' + ' = ' + initial_state_str + ';\n'


def delay__(u : SignalUserTemplate, initial_state = None):
    return wrap_signal( Delay(get_simulation_context(), u.unwrap, initial_state ).outputs[0] )






class Flipflop(bi.BlockPrototype):
    def __init__(self, sim : Simulation, activate_trigger : Signal, disable_trigger : Signal, initial_state = False, nodelay = False ):

        self._nodelay = nodelay
        self._activate_trigger = activate_trigger
        self._disable_trigger  = disable_trigger
        self._initial_state    = initial_state

        bi.BlockPrototype.__init__(self, sim, [ activate_trigger, disable_trigger ], 1)

    def config_request_define_output_types(self, inputTypes):

        return [ dt.DataTypeBoolean(1) ]        

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        if self._nodelay:
            # (direct feedtrough) dependence on all inputs
            return self.inputs
        else:
            # no direct feedthrough
            return []

    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states
        return self.inputs  # all inputs

    def generate_code_defStates(self, language):
        if language == 'c++':
            return self.outputs[0].datatype.cpp_define_variable( self.getUniqueVarnamePrefix() + '_state' )  + ';\n'

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            
            state_varname = self.getUniqueVarnamePrefix() + '_state'

            lines = signals[0].name + ' = ' + state_varname + ';\n'
            if self._nodelay:
                lines += signals[0].name + ' = ' + self.inputs[0].name + ' ? true : ' + signals[0].name + ';\n'
                lines += signals[0].name + ' = ' + self.inputs[1].name + ' ? false : ' + signals[0].name + ';\n'

            return lines

    def generate_code_update(self, language):
        if language == 'c++':

            state_varname = self.getUniqueVarnamePrefix() + '_state'
            lines = state_varname + ' = ' + self.inputs[0].name + ' ? true : ' + state_varname + ';\n'
            lines += state_varname + ' = ' + self.inputs[1].name + ' ? false : ' + state_varname + ';\n'
            return lines

    def generate_code_reset(self, language):
        if language == 'c++':

            if self._initial_state:
                # get the zero element for the given datatype
                initial_state_str = 'true'
            else:
                initial_state_str = 'false'

            return self.getUniqueVarnamePrefix() + '_state' + ' = ' + initial_state_str + ';\n'


def flipflop(activate_trigger : Signal, disable_trigger : Signal, initial_state = False, nodelay = False):
    """
        TODO..
    """
    
    return wrap_signal( Flipflop(get_simulation_context(), activate_trigger.unwrap, disable_trigger.unwrap, initial_state = initial_state, nodelay=nodelay ).outputs[0] )









#
# memory / array to store / read values
#

class Memory(bi.BlockPrototype):
    def __init__(self, sim : Simulation, datatype, constant_array, write_index : Signal = None, value : Signal = None ):

        self._constant_array = constant_array
        self._length         = len(constant_array)
        self._array_datatype = dt.DataTypeArray( self._length, datatype )

        if write_index is None:
            self._static = True
        elif value is not None:
            self._static = False
        else:
            raise BaseException('Memory: write_index was defined but no value to write')

        # call super
        if self._static:
            bi.BlockPrototype.__init__(self, sim, inputSignals = [], N_outputs = 1, output_datatype_list = [self._array_datatype]  )
        else:
            bi.BlockPrototype.__init__(self, sim, inputSignals = [write_index, value], N_outputs = 1, output_datatype_list = [self._array_datatype]  )

        # indicate that the output of this port is passed by reference in c++
        self.outputs[0].set_is_referencing_memory(True)

        self.outputs[0].properties_internal['memory_length'] = self._length

    # TODO: not sure if this is ever beeing called as the output datatypes are already specified in the constructor
    def config_request_define_output_types(self, inputTypes):
        # define the output type 
        return [ self._array_datatype ]

    def config_request_define_feedforward_input_dependencies(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on nothing
        return []
            
    def config_request_define_state_update_input_dependencies(self, outputSignal):
        # return a list of input signals that are required to update the states

        if self._static:
            return []  # no states
        else:
            return [self.inputs[0], self.inputs[1]]

    #
    # code gen
    #

    def generate_code_defStates(self, language):
        if language == 'c++':

            # encode the given data and initialize a C array
            csv_array = ','.join([str(x) for x in self._constant_array])
            return self._array_datatype.cpp_define_variable(  self.getUniqueVarnamePrefix() + '_array' ) + ' {' + csv_array + '};\n'

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            # place a reference
            return cgh.defineVariable( signals[0], make_a_reference=True ) + ' = ' + self.getUniqueVarnamePrefix() + '_array' + ';\n'

    def generate_code_update(self, language):
        if language == 'c++':

            if self._static:
                return ''

            code = '' +  self.inputs[0].datatype.cpp_define_variable(variable_name='tmp') + ' = ' + self.inputs[0].name + ';\n'
            code += cgh.generate_if_else(language, condition_list= ['tmp < 0'], action_list=['tmp = 0;'])
            code += cgh.generate_if_else(language, condition_list= ['tmp >= ' + str(self._length) ], action_list=[ 'tmp = ' + str(self._length-1) + ';' ])

            code += self.getUniqueVarnamePrefix() + '_array[tmp] = ' + self.inputs[1].name + ';\n'

            return cgh.brackets(code)

    def generate_code_reset(self, language):
        if language == 'c++':
            # TODO
            return '// WARNIG: reset of memory not implemented\n'




def memory(datatype, constant_array, write_index : SignalUserTemplate = None, value : SignalUserTemplate = None):
    """
        Define an array

        Allocates static memory for an array of elements given a datatype.
        During each sampling instant, one element can be (over)written. 

        datatype       - the datatype of the array elements
        constant_array - list of constants that contain the data to initialize the array
        write_index    - the array index of the element to replace by value (optional)
        value          - the value to write into the array at write_index (optional)

        returns a reference to the memory segment which is accessible by memory_read()

        Limitations: currently the memory is not reset on subsystem reset. This will change.
    """

    if write_index is not None and value is not None:
        return wrap_signal( Memory(get_simulation_context(), datatype, constant_array, write_index.unwrap, value.unwrap).outputs[0] )
    elif write_index is None and value is None:
        return wrap_signal( Memory(get_simulation_context(), datatype, constant_array).outputs[0] )
    else:
        raise BaseException('memory: write_index and value were not properly defined')




class MemoryRead(bi.StaticFn_NTo1):
    def __init__(self, sim : Simulation, memory : Signal, index : Signal ):

        if 'memory_length' not in memory.properties_internal:
            raise BaseException('No property memory_length in input signal. Please create the input signal using memory()')

        self._length = memory.properties_internal['memory_length']

        # print(' ############# reading a memory of length', self._length)

        bi.StaticFn_NTo1.__init__(self, sim, inputSignals = [memory, index] )

    def config_request_define_output_types(self, inputTypes):
        # returt the datatype of the array elements
        return [ self.inputs[0].getDatatype().datatype_of_elements ]  

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':

            code = '' +  self.inputs[1].datatype.cpp_define_variable(variable_name='tmp') + ' = ' + self.inputs[1].name + ';\n'
            code += cgh.generate_if_else(language, condition_list= ['tmp < 0'], action_list=['tmp = 0;'])
            code += cgh.generate_if_else(language, condition_list= ['tmp >= ' + str(self._length) ], action_list=[ 'tmp = ' + str(self._length-1) + ';' ])

            code += signals[0].name + ' = ' + self.inputs[0].name + '[tmp];\n'
            
            return cgh.brackets(code)

def memory_read( memory : SignalUserTemplate, index : SignalUserTemplate ):
    """
        Read an element from an array defined by memory()

        index - the index indicating the element to read.

        Returns the value of the element
    """
    return wrap_signal( MemoryRead(get_simulation_context(), memory.unwrap, index.unwrap ).outputs[0] )


