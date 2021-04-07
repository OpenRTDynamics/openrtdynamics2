from .diagram_core.system import System
from .diagram_core import datatypes as dt
from .diagram_core.signal_network.signals import Signal
from .diagram_core import code_generation_helper as cgh
from . import block_interface as bi

from typing import Dict, List




class SystemWrapper:

    def __init__(self, system : System):

        self._system = system

        # info that becomes available after callback_on_system_compiled() is called
        self._manifest = None
        self._instance_varname = None
        self._inputs = None

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._system.primary_outputs

    @property
    def system_name(self):
        return self._system.name

    def callback_on_system_compiled(self, unique_variable_prefix : str):

        self._inputs           = self._system.compile_result.inputSignals
        self._manifest         = self._system.compile_result.manifest
        self._instance_varname = unique_variable_prefix + '_subsystem_' + self._manifest.API_name

        # input signals for calculating the outputs and updating the states. The lists are ordered
        self.inputs_to_calculate_outputs = self._system.compile_result.simulationInputSignalsToCalculateOutputs
        self.inputs_to_update_states     = self._system.compile_result.simulationInputSignalsToUpdateStates


    def generate_code_defStates(self, language):
        if language == 'c++':
            lines = '// instance of ' + self._manifest.API_name + '\n'
            lines += self._manifest.API_name + ' ' + self._instance_varname + ';\n'

            return lines

    def generate_code_reset(self, language):
        if language == 'c++':
            return self._instance_varname + '.' + self._manifest.getAPIFunctionName('reset') +  '();\n'

    def generate_code_update(self, language):
        return self._instance_varname + '.' + self._manifest.getAPIFunctionName('state_update') +  '(' + cgh.signal_list_to_names_string(self.inputs_to_update_states) + ');\n'

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = ''
            
            #
            # TO THINK ABOUT: 2.5.2020: concept: how to compute only the necessary signals?
            #

            #
            # REWORK 30.3.2021: introduce call to fn(Inputs & inputs, Outputs & outputs)
            # and remove the prev. style
            #

            # create temporary variables for each output signal
            output_variable_names = []

            for s in self.outputs: # for each output of the subsystem reservate a variable

                if s not in signals:
                    lines += '// NOTE: unused output signal' + s.name + '\n'
                else:
                    lines += ''                

                output_var_name = '_' + s.name
                output_variable_names.append( output_var_name )
                lines +=  s.datatype.cpp_define_variable( output_var_name ) + ';\n'


            lines += cgh.call_function_from_varnames(
                fn_name = self._instance_varname + '.' + self._manifest.getAPIFunctionName('calculate_output'),
                input_names = cgh.signal_list_to_name_list(self.inputs_to_calculate_outputs),
                output_names = output_variable_names
            )

        return lines, output_variable_names






# NOTE: check if this might be helpful, otherwise remove
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
        if not signal.getDatatype().cpp_datatype_string == dependingInput_cpptype:
            raise BaseException('datatype does not match the one specified in the manifest. (' + (dependingInput_cpptype) + ' is required in the manifest)' )

        # append signal
        dependingInputs.append( signal ) 

    return dependingInputs




# helper fn for classes that are derived from SingleSubsystemEmbedder and XX
def embed_subsystem(
    language, 
    system_wrapper : SystemWrapper, 
    assign_to_signals=None, 
    assign_to_variable_names=None,
    indices_of_output_signals_of_subsystem=None, 
    calculate_outputs = True, 
    update_states = False, 
    reset_states=False
):
    """  
        generate code to call a subsystem given a system wrapper

        - system_wrapper      - the system wrapper including the subsystem - type: : dy.SystemWrapper
        - assign_to_signals / assign_to_variable_names   
             - list of signals / variable names to which the output signals of the subsystem are assigned to
        
        - indices_of_output_signals_of_subsystem - the indices of the output signals of the embedded subsystem

        - calculate_outputs   - generate a call to the output computation API function of the subsystem
        - update_states       - generate a call to the state update API function of the subsystem
    """


    lines = '{ // subsystem ' + system_wrapper.system_name + '\n'

    innerLines = ''

    #
    # system_prototype is of type SystemWrapper. call the code generation routine of the subsystem
    #

    if reset_states:
        innerLines += system_wrapper.generate_code_reset(language)


    # generate code for calculating the outputs 
    if calculate_outputs:

        # extract the signals names
        if assign_to_signals is not None and assign_to_variable_names is None:
            assign_to_variable_names = cgh.signal_list_to_name_list(assign_to_signals)
        elif assign_to_variable_names is not None:
            pass
        else:   
            raise BaseException('incorrect call')


        wrapper_code, output_variable_names_of_subsystem = system_wrapper.generate_code_output_list(language, system_wrapper.outputs)
        innerLines += wrapper_code

        # copy the output values of the subsystem to the variables name 'assign_to_variable_names'
        for i in range( 0, len( indices_of_output_signals_of_subsystem ) ):

            output_signal_index = indices_of_output_signals_of_subsystem[i]
            output_variable_name_of_subsystem = output_variable_names_of_subsystem[output_signal_index]

            innerLines += cgh.assign( output_variable_name_of_subsystem, assign_to_variable_names[i] )

    # generate code for updating the states
    if update_states:
        innerLines += system_wrapper.generate_code_update(language)


    lines += cgh.indent(innerLines)
    lines += '}\n'

    return lines





#
# helper functions for both SingleSubsystemEmbedder and XX
#

def setup_output_datatype_inheritance( normal_outputs_of_embedding_block, subsystem_prototype ):
    # inherit output datatypes of this block from the embedded subsystem described by subsystem_prototype

    for i in range(0, len(normal_outputs_of_embedding_block) ):

        output_signal_of_embedding_block = normal_outputs_of_embedding_block[i]
        output_signal_of_subsystem = subsystem_prototype.outputs[i]
        output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )

    return


class OutputMapEmbeddingBlockToSubsystem():

    def __init__(self, normal_outputs_of_embedding_block, subsystem_prototype):

        self._output_signal_mapping, self._output_signal_index_mapping = self.create_output_mapping_table(normal_outputs_of_embedding_block, subsystem_prototype )


    def create_output_mapping_table(self, normal_outputs_of_embedding_block, subsystem_prototype ):
        # output signal mapping: map each output of SingleSubsystemEmbedder to an output of the subsystem
        output_signal_mapping = {}

        # map output signal of embedding block to output index of the embedded block
        output_signal_index_mapping = {}

        for i in range(0, len(normal_outputs_of_embedding_block) ):
            # fill in mapping table
            
            if subsystem_prototype is not None:
                output_signal_mapping[ normal_outputs_of_embedding_block[i] ] = subsystem_prototype.outputs[i]

            output_signal_index_mapping[ normal_outputs_of_embedding_block[i] ] = i



        return output_signal_mapping, output_signal_index_mapping


    def map(self, output_signals_of_embedding_block):
        """

            given the signals to calculate (variable signals) in the callbacks 

                def generate_code_output_list(self, language, signals : List [ Signal ] ): 

            resolve the mapping to the embedded subsystems output signals

        """

        mapped_subsystem_output_signals = []
        for s in output_signals_of_embedding_block:
            mapped_subsystem_output_signals.append( self._output_signal_mapping[s] )

        return mapped_subsystem_output_signals
    


    def map_to_output_index(self, output_signals_of_embedding_block):
        """
            return a mapping to indices of the block outputs:

            e.g. [sig0, sig1, sig2, sig4] --> [0, 1, 2, 4]
        """

        mapped_subsystem_output_signals = []
        for s in output_signals_of_embedding_block:
            mapped_subsystem_output_signals.append( self._output_signal_index_mapping[s] )

        return mapped_subsystem_output_signals
    








#
# Subsystem prototypes
#



# class GenericSubsystem(bi.BlockPrototype):
#     """
#         Include a sub-system by passing a manifest

#         - sim - the simulation this block is embedded into

#         parameters required only in case the subsystem is already defined (e.g. loaded from a library):

#         - manifest           - the manifest of the subsystem to include (optional, might be handed over by init())
#         - inputSignals       - the inputs to the subsystem 
#         - N_outputs          - prepare a number of nOutputs (optional in case a manifest is given)
#         - embedded_subsystem - the system to embed (optional in case a manifest to an already compiled subsystem is given, NOT IMPLEMENTED)

#         Note: the number of outputs must be defined either by N_outputs or by a manifest

#     """
#     def __init__(self, sim : System = None, manifest=None, inputSignals=None, N_outputs = None, embedded_subsystem=None ):

#         self.manifest = manifest
#         self.inputSignals = inputSignals
#         self.sim = sim
#         self.Noutputs = N_outputs
#         self._embedded_subsystem = embedded_subsystem

#         if manifest is not None:
#             if N_outputs is None:
#                 self.Noutputs = self.manifest.number_of_default_ouputs
#             else:
#                 raise BaseException("N_outputs and a manifest specified at the same time")

#         # # output signals that were created by sth. ourside of this prototype
#         # # and that need to be connected to the actual outputs when init() is called.
#         # self.anonymous_output_signals = None

#         # optional (in case this block is in charge of putting the code for the subsystem)
#         self.compileResult = None

#         # init super class
#         bi.BlockPrototype.__init__(self, self.sim, N_outputs = self.Noutputs)

#         # Note: the inputSignals are not defined when subsystems are pre-defined in the code
#         # but are automatically placed and connected by the compiler during compilation

#         # check if it is already possible to init this prototype
#         # (in case all requred information is available)
#         if inputSignals is not None and manifest is not None:
#             self.init()

#         # configure datatype inheritance for the outputs signals
#         for i in range(0, len( embedded_subsystem.primary_outputs )):

#             output_signal_of_embedding_block = self.outputs[i]
#             output_signal_of_subsystem = embedded_subsystem.primary_outputs[i]

#             output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )

#     @property
#     def embedded_subsystem(self):
#         """
#             Return the system that is embedded (in case it was provided, returns None otherwise)
#         """

#         return self._embedded_subsystem

#     def compile_callback_all_subsystems_compiled(self):

#         embedded_system = self._embedded_subsystem
#         #
#         # continue init as now all subsystems are compiled and the compile results and the manifest of
#         # the system to compile is available.
#         #
#         self.init(embedded_system.compile_result.manifest, embedded_system.compile_result, embedded_system.compile_result.inputSignals)

#     # post_compile_callback (called after the subsystem to embed was compiled)
#     def init(self, manifest, compileResult, inputSignals):
#         """
#             This is a second phase initialization of this subsystem block 
#             (to be called by compile_callback_all_subsystems_compiled())

#             This function shall be called when the subsystem to embed is compiled
#             after the instance of 'GenericSubsystem' is created. This way, it is possible
#             to add blocks embeddeding sub-systems without haveing these subsystems to be
#             already compiled.

#             Optionally, the system this block belongs to can be set.

#             manifest       - the system manifest of the subsystem to embed
#             compileResults - the compile results of the subsystem to embed
#             inputSignals   - input signals to the subsystem to embed (links comming from an upper-level subsystem)

#         """        

#         #
#         #    set the manifest of the subsystem
#         #
#         if self.manifest is not None:
#             raise BaseException("cannot call this function as the subsystem's manifest was already defined in the constructor.")

#         self.manifest = manifest

#         #
#         #    Set the compilation result of the embedded system (if available)
#         #
#         self.compileResult = compileResult

#         #
#         #    connect the inputs (coming from the upper-level system)
#         #

#         if self.inputSignals is not None:
#             raise BaseException("The subsystem's inputSignals were already specified in the constructor.")

#         self.inputSignals = inputSignals



        # def collectDependingSignals(signals, manifestFunctionInputs):
        #     # collect all depending input signals (that are needed to calculate the output) in a list
        #     # MOVE TO A FUNCTION. MAYBE MOVE TO MANIFEST.PY
        #     dependingInputs = []
        #     for i in range( len(manifestFunctionInputs['names']) ):

        #         dependingInput_name = manifestFunctionInputs['names'][i]
        #         dependingInput_type = manifestFunctionInputs['types'][i]
        #         dependingInput_cpptype = manifestFunctionInputs['cpptypes'][i]

        #         # TODO: CHECK FOR FAILING LOOKUP
        #         signal = signals[ dependingInput_name ]

        #         # check datatype
        #         if not signal.getDatatype().cpp_datatype_string == dependingInput_cpptype:
        #             raise BaseException('datatype does not match the one specified in the manifest. (' + (dependingInput_cpptype) + ' is required in the manifest)' )

        #         # append signal
        #         dependingInputs.append( signal ) 

        #     return dependingInputs



    #     # verify the number of outputs of the embedded system
    #     number_of_outputs_as_described_by_manifest = self.manifest.number_of_default_ouputs

    #     if not number_of_outputs_as_described_by_manifest == self.Noutputs:
    #         BaseException("missmatch in the number of outputs")

    #     # get the output datatypes of the embedded system
    #     self.outputTypes = self.manifest.io_outputs['calculate_output']['types']  


    #     if self.compileResult is None:
    #         # collect all depending input signals (that are needed to calculate the output) in a list
    #         self.inputsToCalculateOutputs = collectDependingSignals( self.inputSignals, self.manifest.io_inputs['calculate_output'] )

    #         # collect all inputs required to perform the state update
    #         self.inputsToUpdateStates = collectDependingSignals( self.inputSignals, self.manifest.io_inputs['state_update'] )

    #     else:
    #         # use the available compile results to get the I/O signals
    #         # in this case, self.inputSignals shall be a list of signals. The order
    #         # shall match the signal order in self.compileResults.inputSignals

    #         self.inputsToCalculateOutputs = self.compileResult.simulationInputSignalsToCalculateOutputs
    #         self.inputsToUpdateStates = self.compileResult.simulationInputSignalsToUpdateStates

            

    #     # combine all inputs to a list
    #     self.allInputs = list()

    #     self.allInputs.extend( self.inputsToCalculateOutputs )
    #     self.allInputs.extend( self.inputsToUpdateStates )

    #     #
    #     # now initialize the prototype
    #     #

    #     # define the inputs
    #     self.update_input_config( self.allInputs )

    #     # for code generation
    #     self.instanceVarname = self.getUniqueVarnamePrefix() + '_subsystem_' + self.manifest.API_name


    # def config_request_define_output_types(self, inputTypes):

    #     # the datatypes are fixed in the manifest 
    #     return self.outputTypes        

    # def config_request_define_feedforward_input_dependencies(self, outputSignal):

    #     # NOTE: This is a simplified veriant so far.. no dependence on the given 'outputSignal'
    #     #       (Every output depends on every signal in self.inputsToCalculateOutputs)

    #     # TODO: 6.10.19 implement this in a more granular way.
    #     # also use self.compileResults to get those information

    #     return self.inputsToCalculateOutputs

    # def config_request_define_state_update_input_dependencies(self, outputSignal):
 
    #     # return a list of input signals that are required to update the states
    #     return self.inputsToUpdateStates



    # def codegen_addToNamespace(self, language):
    #     lines = ''

    #     # putting code for subsystems is performed using execution commands

    #     return lines

    # def generate_code_defStates(self, language):
    #     if language == 'c++':
    #         lines = '// instance of ' + self.manifest.API_name + '\n'
    #         lines += self.manifest.API_name + ' ' + self.instanceVarname + ';\n'

    #         return lines

    # def generate_code_reset(self, language):
    #     if language == 'c++':
    #         return self.instanceVarname + '.' + self.manifest.getAPIFunctionName('reset') +  '();\n'


    # def generate_code_init(self, language):
    #     pass


    # def generate_code_destruct(self, language):
    #     pass


    # # helper fn to build code
    # def generate_code_call_OutputFunction(self, instanceVarname, manifest, language):
    #     return instanceVarname + '.' + manifest.getAPIFunctionName('calculate_output') +  '(' + cgh.signal_list_to_names_string(self.outputs + self.inputsToCalculateOutputs) + ');\n'

    # # helper fn to build code
    # def generate_code_call_UpdateFunction(self, instanceVarname, manifest, language):
    #     return instanceVarname + '.' + manifest.getAPIFunctionName('state_update') +  '(' + cgh.signal_list_to_names_string(self.inputsToUpdateStates) + ');\n'

    # def generate_code_output_list(self, language, signals : List [ Signal ] ):

    #     if language == 'c++':
    #         lines = ''
            
    #         #
    #         # TODO: 2.5.2020: concept: how to compute only the nescessary signals?
    #         #


    #         #
    #         # REWORK: introduce call to fn(Inputs & inputs, Outputs & outputs)
    #         # and remove the prev. style
    #         #

    #         for s in self.outputs: # for each output of the subsystem reservate a variable
    #             lines += cgh.define_variable_line( s ) 

    #             if s not in signals:
    #                 lines += '// NOTE: unused output signal' + s.name + '\n'
    #             else:
    #                 lines += ''                

    #         lines += self.generate_code_call_OutputFunction(self.instanceVarname, self.manifest, language)

    #     return lines

    # def generate_code_update(self, language):
    #     if language == 'c++':

    #         # input to this call are the signals in self.inputsToUpdateStates
    #         return self.generate_code_call_UpdateFunction(self.instanceVarname, self.manifest, language)














