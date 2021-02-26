from .diagram_core.system import System
from .diagram_core import datatypes as dt
from .diagram_core.signal_network.signals import Signal
from .diagram_core import code_generation_helper as cgh
from . import block_interface as bi

from .block_prototypes_subsystems import *
from .block_prototypes_single_subsystem import *
from .block_prototypes_switched_subsystems import *

from typing import Dict, List

# TODO: rename to atomic_blocks

"""
    This file contains the implementations (i.e., functionality for code generation) of elementary blocks.
    The user-interface(s) for each of the blocks is in core_blocks.py
"""











# # REMOVE THIS
# def embed_subsystem(language, system_prototype, ouput_signals_name=None, calculate_outputs = True, update_states = False ):
#     """  
#         generate code to call a subsystem (TODO: this is obsolete remove it!)

#         - system_prototype   - the block prototype including the subsystem - type: : dy.GenericSubsystem
#         - ouput_signals_name - list of variable names to which the output signals of the subsystem are assigned to
#         - calculate_outputs  - generate a call to the output computation API function of the subsystem
#         - update_states      - generate a call to the state update API function of the subsystem
#     """


#     lines = '{ // subsystem ' + system_prototype.embedded_subsystem.name + '\n'

#     innerLines = ''

#     #
#     # system_prototype is of type GenericSubsystem. call the code generation routine of the subsystem
#     #

#     # generate code for calculating the outputs 
#     if calculate_outputs:

#         innerLines += system_prototype.generate_code_output_list(language, system_prototype.outputs)

#         if len(system_prototype.outputs) != len(ouput_signals_name):
#             raise BaseException('len(system_prototype.outputs) != len(ouput_signals_name)')




#         for i in range( 0, len( ouput_signals_name ) ): # NOTE:
#             innerLines += asign( system_prototype.outputs[i].name, ouput_signals_name[i] )

#     # generate code for updating the states
#     if update_states:
#         innerLines += system_prototype.generate_code_update(language)


#     lines += indent(innerLines)
#     lines += '}\n'

#     return lines









class TruggeredSubsystem(SingleSubsystemEmbedder):
    """
        Include a triggered sub-system

        Optional:

            prevent_output_computation = True: 
                The subsystems outputs are only computed when triggered. Please note that the outputs
                of the subsystem are uninitialized until the subsystem is triggered for the first time.

    """

    def __init__(self, sim : System, control_input : Signal, subsystem_prototype : GenericSubsystem,  prevent_output_computation = False ):
        
        self._control_input = control_input
        self.prevent_output_computation = prevent_output_computation

        SingleSubsystemEmbedder.__init__(self, sim, 
                                        control_inputs=[control_input], 
                                        subsystem_prototype=subsystem_prototype, 
                                        number_of_control_outputs=0 )


    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':
            
            # generate code to call subsystem output(s)
            code_compute_output = embed_subsystem3(
                language, 
                subsystem_prototype=self._subsystem_prototype, 
                assign_to_signals=signals, 
                ouput_signals_of_subsystem=self.outputs_map_from_embedding_block_to_subsystem.map( signals ),
                calculate_outputs = True, update_states = False 
            )

            if self.prevent_output_computation:

                # the subsystems outputs are only computed when triggered
                lines += cgh.generate_if_else(language, 
                    condition_list=[ cgh.generate_compare_equality_to_constant( language, self._control_input.name, 1 ) ], 
                    action_list=[ code_compute_output ])

                # TODO: Design choice: assign NAN to the output values for self._control_input.name == 0 ?

            else:
                # the subsystems outputs are always computed
                lines += code_compute_output


        return lines

    def generate_code_update(self, language):

        lines = ''
        if language == 'c++':

            # generate code to compute the state update of the subsystem
            code_compute_state_update = embed_subsystem3(
                language, 
                subsystem_prototype=self._subsystem_prototype, 
                calculate_outputs = False, update_states = True
            )

            # the subsystems update is only performed when triggered
            lines += cgh.generate_if_else(language, 
                condition_list=[ cgh.generate_compare_equality_to_constant( language, self._control_input.name, 1 ) ], 
                action_list=[ code_compute_state_update ])

        return lines






class LoopUntilSubsystem(SingleSubsystemEmbedder):
    """
        Embed a loop sub-system

    """

    def __init__(self, sim : System, max_iterations : int, 
                    subsystem_prototype : GenericSubsystem, 
                    until_signal : Signal = None, yield_signal : Signal = None ):
        
        self.max_iter = max_iterations
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


    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':

            assign_to_signals = []
            ouput_signals_of_subsystem = []

            assign_to_signals.extend(signals)
            ouput_signals_of_subsystem.extend(self.outputs_map_from_embedding_block_to_subsystem.map( signals )) # output signal mapping lookup

            control_output_index = 0

            if self._until_signal is not None:
                # define tmp-var for self._until_signal instead of a block output
                lines += cgh.defineVariables( [self._until_signal] )

                # add list of signals to assign
                assign_to_signals.append( self._until_signal )
                ouput_signals_of_subsystem.append( self._control_signals_from_embeded_system[control_output_index] )
            
                control_output_index += 1


            if self._yield_signal is not None:
                # define tmp-var for self._yield_signal instead of a block output
                lines += cgh.defineVariables( [self._yield_signal] )

                # add list of signals to assign
                assign_to_signals.append( self._yield_signal )
                ouput_signals_of_subsystem.append( self._control_signals_from_embeded_system[control_output_index] )

                control_output_index += 1



            calc_outputs = embed_subsystem3(
                language, 
                subsystem_prototype=self._subsystem_prototype, 
                assign_to_signals=assign_to_signals, 
                ouput_signals_of_subsystem=ouput_signals_of_subsystem,
                calculate_outputs = True, update_states = False
            )

            

            update_states = embed_subsystem3(
                language, 
                subsystem_prototype=self._subsystem_prototype, 
                calculate_outputs = False, update_states = True
            )

            code = ''
            code +=  calc_outputs 
            code += update_states

            if self._yield_signal is not None:
                code += cgh.generate_loop_break(language, condition=self._yield_signal.name)

            if self._until_signal is not None:

                code_reset_subsystem = embed_subsystem3(
                    language, 
                    subsystem_prototype=self._subsystem_prototype, 
                    calculate_outputs = False, update_states = False,
                    reset_states = True
                )

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
























class SwitchSubsystems(MultiSubsystemEmbedder):
    """
        A system that embeds multiple subsystems and a control input to switch in-between.
        The outputs of the currently active subsystem are forwarded.
    """

    def __init__(self, sim : System, control_input : Signal, subsystem_prototypes : List [GenericSubsystem], reference_outputs : List [Signal] ):
        
        self._control_input = control_input

        MultiSubsystemEmbedder.__init__(self, sim, 
                                        control_inputs=[control_input], 
                                        subsystem_prototypes=subsystem_prototypes, 
                                        switch_reference_outputs=reference_outputs,
                                        number_of_control_outputs=0 )

    def generate_code_defStates(self, language):
        lines = MultiSubsystemEmbedder.generate_code_defStates(self, language)
        
        return lines

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':
            
            lines += self.codegen_help_generate_switch( 
                language=language,
                switch_control_signal_name=self._control_input.name,
                switch_ouput_signals=signals,
                additional_outputs=[],
                calculate_outputs = True, update_states = False
            )

        return lines

    def generate_code_update(self, language):

        lines = ''
        if language == 'c++':

            lines += self.codegen_help_generate_switch(
                language=language, 
                switch_control_signal_name=self._control_input.name,
                calculate_outputs=False, 
                update_states=True
            )

        return lines







class StatemachineSwitchSubsystems(MultiSubsystemEmbedder):
    """
        Implement a state machine in which the states are represented by subsystems.
        State transitions are performed in case a special control output of the currently
        active subsystem indicates a transition to the next state.

        self.state_output  - 
    """

    def __init__(self, sim : System, subsystem_prototypes : List [GenericSubsystem], reference_outputs : List [Signal] ):
        
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
        return self.control_outputs[0]


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

            lines += self.codegen_help_generate_switch( language=language, 
                                            switch_control_signal_name=  self._state_memory ,
                                            switch_ouput_signals=signals,
                                            additional_outputs=[self.state_output] )

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

            lines += self.codegen_help_generate_switch(
                language=language, 
                switch_control_signal_name=self._state_memory,
                calculate_outputs=False, 
                update_states=True
            )

            # get the signal issued by the currently active subsystem that describes the requests for a stare transition
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
    def __init__(self, sim : System, constant, datatype ):

        self.constant = constant

        # call super
        bi.StaticSource_To1.__init__(self, sim, datatype)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str( self.constant ) + ';\n'





#
# Multiply by constant
#

class Gain(bi.StaticFn_1To1):
    def __init__(self, sim : System, u : Signal, factor : float ):

        self._factor = factor

        bi.StaticFn_1To1.__init__(self, sim, u)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._factor) + ' * ' + self.inputs[0].name +  ';\n'





#
# Cast to given datatype
#

class ConvertDatatype(bi.StaticFn_1To1):
    def __init__(self, sim : System, u : Signal, target_type : dt.DataType ):

        self._target_type = target_type

        bi.StaticFn_1To1.__init__(self, sim, u)

    def config_request_define_output_types(self, inputTypes):
        return [ self._target_type ]  

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            # TODO: only = is used and the c++ compiler decides how to convert...
            return signals[0].name + ' = ' + self.inputs[0].name + ';\n'



#
# Basic operators
#

class Add(bi.StaticFn_NTo1):
    def __init__(self, sim : System, inputSignals : List[Signal], factors : List[float] ):

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



class Operator1(bi.StaticFn_NTo1):
    def __init__(self, sim : System, inputSignals : List[Signal], operator : str ):

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












class ComparisionOperator(bi.StaticFn_NTo1):
    def __init__(self, sim : System, left : Signal, right : Signal, operator : str ):

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




class SwitchNto1(bi.StaticFn_NTo1):
    def __init__(self, sim : System, state : Signal, inputs : List [Signal] ):

        self.inputs = inputs
        self.state = state

        inputSignals = [state]
        inputSignals.extend(inputs)

        bi.StaticFn_NTo1.__init__(self, sim, inputSignals )

    def config_request_define_output_types(self, inputTypes):

        # check weather the trigger input is int32
        if inputTypes[0] is not None:
            if dt.DataTypeInt32(1).is_equal_to( inputTypes[0] ) == 0:
                raise BaseException('state input must be of type Int32')  

        # determine a guess for the output datatype
        # check if all given datatypes are equal
        autoDatatype = get_unique_datatype_from_io_typespe_from_io_types(self.outputs[0].getDatatype(), inputTypes[1:-1] )

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



class ConditionalOverwrite(bi.StaticFn_NTo1):
    def __init__(self, sim : System, signal : Signal, condition : Signal, new_value ):

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




#
# Static functions that map 1 --> 1
#

class StaticFnByName_1To1(bi.StaticFn_1To1):
    def __init__(self, sim : System, u : Signal, functionName : str ):

        self._functionName = functionName

        bi.StaticFn_1To1.__init__(self, sim, u)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._functionName) + '(' + self.inputs[0].name +  ');\n'




class Operator0(bi.StaticFn_1To1):
    def __init__(self, sim : System, u : Signal, operator_str : str ):

        self._operator_str = operator_str

        bi.StaticFn_1To1.__init__(self, sim, u)

    def generate_code_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._operator_str) + self.inputs[0].name +  ';\n'






#
# static functinos that map 2 --> 1
#

class StaticFnByName_2To1(bi.StaticFn_NTo1):
    def __init__(self, sim : System, left : Signal, right : Signal, function_name : str ):

        self._function_name = function_name

        bi.StaticFn_NTo1.__init__(self, sim, inputSignals = [left, right])

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = signals[0].name + ' = ' + self._function_name + '(' + self.inputSignals[0].name +  ', ' + self.inputSignals[1].name + ')' + ';\n'
            return lines








class GenericCppFunctionCall(bi.BlockPrototype):
    def __init__(
        self, 
        system : System, 
        input_signals : List[Signal], 
        input_names : List [str], 
        input_types, 
        output_names : List[str], 
        output_types, 
        function_name : str
    ):

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

        bi.BlockPrototype.__init__(self, system, input_signals, len(output_names), output_types  )

        self._function_name = function_name

    def config_request_define_output_types(self, inputTypes):

        for i in range(0, len(inputTypes)):
            if inputTypes[i] is not None and not inputTypes[i].is_equal_to( self._input_types[i] ):
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

    def generate_code_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':

            ilines = ''

            # create tmp output variables
            tmp_output_variable_names = []
            for i in range(0, len(self._output_names)):
                tmp_variable_name = self._function_name + '_' + self._output_names[i]
                tmp_output_variable_names.append( tmp_variable_name )
                ilines += self._output_types[i].cpp_define_variable(variable_name=tmp_variable_name) + ';\n'

            # function call
            ilines += cgh.call_function_from_varnames( self._function_name, cgh.signal_list_to_name_list(self.inputs), tmp_output_variable_names)

            # copy outputs from tmp variables
            for i in range(0, len(self._output_names)):

                # only copy the needed outputs as indicated by 'signals'
                if self.outputs[i] in signals:
                    ilines += self.outputs[i].name + ' = ' + tmp_output_variable_names[i] + ';\n'

            return '{ // calling the static function ' + self._function_name + '\n' + cgh.indent(ilines) + '}\n'




class GenericCppStatic(GenericCppFunctionCall):
    def __init__(
        self, 
        system : System, 
        input_signals : List[Signal], 
        input_names : List [str], 
        input_types, 
        output_names : List[str], 
        output_types, 
        cpp_source_code : str
    ):

        GenericCppFunctionCall.__init__(
            self, 
            system, 
            input_signals, input_names, input_types, 
            output_names, output_types,
            function_name = None # self._static_function_name
        )

        self._cpp_source_code = cpp_source_code
        self._static_function_name = 'fn_static_' + str(self.id)

        #
        self._function_name = self._static_function_name


    def codegen_addToNamespace(self, language):

        if language == 'c++':
            ilines = ''

            info_comment_1 = '// begin of user defined function\n'
            info_comment_2 = '\n// end of user defined function\n'

            ilines += cgh.cpp_define_function_from_types(self._static_function_name, self._input_types, self._input_names, self._output_types, self._output_names, info_comment_1 + self._cpp_source_code + info_comment_2 )

            return ilines





#
# Blocks that have an internal memory
#



class Delay(bi.BlockPrototype):
    def __init__(self, sim : System, u : Signal, initial_state = None ):

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








class Flipflop(bi.BlockPrototype):
    def __init__(self, sim : System, activate_trigger : Signal, disable_trigger : Signal, initial_state = False, nodelay = False ):

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




#
# memory / array to store / read values
#

class Memory(bi.BlockPrototype):
    def __init__(self, sim : System, datatype, constant_array, write_index : Signal = None, value : Signal = None ):

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






class MemoryRead(bi.StaticFn_NTo1):
    def __init__(self, sim : System, memory : Signal, index : Signal ):

        if 'memory_length' not in memory.properties_internal:
            raise BaseException('No property memory_length in input signal. Please create the input signal using memory()')

        self._length = memory.properties_internal['memory_length']

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



