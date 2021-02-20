from .block_prototypes import *
from .signal_interface import SignalUserTemplate, wrap_signal, wrap_signal_list, unwrap_hash, unwrap_list, unwrap
from . import system_context as dy
from .diagram_core import datatypes as dt

from typing import Dict, List


"""
    Core functions which directly point to blocks (implementation in, e.g., c++) 
"""


def generic_subsystem( manifest, inputSignals : List[SignalUserTemplate] ):
    return wrap_signal_list( GenericSubsystem(dy.get_system_context(), manifest, unwrap_hash(inputSignals) ).outputSignals )

def const(constant, datatype ):
    return wrap_signal( Const(dy.get_system_context(), constant, datatype).outputs[0] )

def gain(u : SignalUserTemplate, gain : float ):
    return wrap_signal( Gain(dy.get_system_context(), u.unwrap, gain).outputs[0] )

def convert(u : SignalUserTemplate, target_type : dt.DataType ):
    """
    Datatype conversion

    The input is converted to the given datatype

    u           - the input signal
    target_type - the datatype
    """
    return wrap_signal( ConvertDatatype(dy.get_system_context(), u.unwrap, target_type).outputs[0] )

def add(input_signals : List[SignalUserTemplate], factors : List[float]):
    """
    Linear combination of the list of input signals with the list of factors

    the output is given by
        input_signals[0] * factors[0] + input_signals[1] * factors[1] + ...
    """
    return wrap_signal( Add(dy.get_system_context(), unwrap_list( input_signals ), factors).outputs[0] )

def operator1(inputSignals : List[SignalUserTemplate], operator : str ):
    return wrap_signal( Operator1(dy.get_system_context(), unwrap_list( inputSignals ), operator).outputs[0] )


#
# logic operators
#

def logic_and(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        logical and

        u1 && u2
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list([u1,u2]), operator=' && ').outputs[0] )

def logic_or(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        logical or
    
        u1 || u2
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list( [u1,u2] ), operator=' || ').outputs[0] )


def logic_xor(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        exclusive logical or (xor)
    
        u1 ^ u2
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list( [u1,u2] ), operator=' ^ ').outputs[0] )


def bitwise_and(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        bitwise and

        u1 & u2
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list([u1,u2]), operator=' & ').outputs[0] )

def bitwise_or(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        bitwise or
    
        u1 | u2
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list( [u1,u2] ), operator=' | ').outputs[0] )


def bitwise_shift_left(u : SignalUserTemplate, shift : SignalUserTemplate):
    """
        logical shift left
    
        u << shift
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list( [u,shift] ), operator=' << ').outputs[0] )


def bitwise_shift_right(u : SignalUserTemplate, shift : SignalUserTemplate):
    """
        logical shift left
    
        u >> shift
    """

    return wrap_signal( Operator1(dy.get_system_context(), inputSignals=unwrap_list( [u,shift] ), operator=' >> ').outputs[0] )









def comparison(left : SignalUserTemplate, right : SignalUserTemplate, operator : str ):
    return wrap_signal( ComparisionOperator(dy.get_system_context(), left.unwrap, right.unwrap, operator).outputs[0] )

def switchNto1( state : SignalUserTemplate, inputs : SignalUserTemplate ):
    return wrap_signal( SwitchNto1(dy.get_system_context(), state.unwrap, unwrap_list(inputs) ).outputs[0] )

def conditional_overwrite(signal : SignalUserTemplate, condition : SignalUserTemplate, new_value ):
    """
    Overwrite the input signal by a given value in case a condition is true

    The output is given by

        signal     for condition==false
        new_value  for condition==true

    """

    if isinstance(new_value, SignalUserTemplate):
        new_value = new_value.unwrap

    return wrap_signal( ConditionalOverwrite(dy.get_system_context(), signal.unwrap, condition.unwrap, new_value).outputs[0] )

def sqrt(u : SignalUserTemplate ):
    """
    Square root
    """
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'sqrt').outputs[0] )

def sin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'sin').outputs[0] )

def cos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'cos').outputs[0] )

def tan(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'tan').outputs[0] )

def atan(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'atan').outputs[0] )

def asin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'asin').outputs[0] )

def acos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'acos').outputs[0] )

def abs(u : SignalUserTemplate ):
    """
    Absolute value

    |u|
    """
    return wrap_signal( StaticFnByName_1To1(dy.get_system_context(), u.unwrap, 'abs').outputs[0] )



def logic_not(u : SignalUserTemplate ):
    """
        logic negation
    """
    return wrap_signal( Operator0(dy.get_system_context(), u.unwrap, '!').outputs[0] )

def bitwise_not(u : SignalUserTemplate ):
    """
    Bitwise not operator

    '~'
    """
    return wrap_signal( Operator0(dy.get_system_context(), u.unwrap, '~').outputs[0] )


def atan2(y : SignalUserTemplate, x : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_2To1(dy.get_system_context(), y.unwrap, x.unwrap, 'atan2').outputs[0] )

def pow(base : SignalUserTemplate, power : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_2To1(dy.get_system_context(), base.unwrap, power.unwrap, 'pow').outputs[0] )

def fmod(x : SignalUserTemplate, y : SignalUserTemplate ):
    """
        modulo function for floating point values

        This function returns the remainder of dividing x/y.
    """
    return wrap_signal( StaticFnByName_2To1(dy.get_system_context(), x.unwrap, y.unwrap, 'fmod').outputs[0] )

def generic_cpp_static(input_signals : List[SignalUserTemplate], input_names : List [str], input_types, output_types, output_names, cpp_source_code : str ):
    """
    Embed C/C++ source code (stateless code only)

    Example:

        source_code = \"\"\"

            // c++ code

            output1 = value;
            if (someinput > value) {
                output2 = value;
            } else {
                output2 = someinput;
            }
            output3 = 0.0;

        \"\"\"

        outputs = dy.generic_cpp_static(input_signals=[ someinput, value ], input_names=[ 'someinput', 'value' ], 
                            input_types=[ dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ], 
                            output_names=['output1', 'output2', 'output3'],
                            output_types=[ dy.DataTypeFloat64(1), dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ],
                            cpp_source_code = source_code )

        output1 = outputs[0]
        output2 = outputs[1]
        output3 = outputs[2]
    """
    return wrap_signal_list( GenericCppStatic(dy.get_system_context(), unwrap_list(input_signals), input_names, input_types, output_names, output_types, cpp_source_code  ).outputs )

def delay__(u : SignalUserTemplate, initial_state = None):
    return wrap_signal( Delay(dy.get_system_context(), u.unwrap, initial_state ).outputs[0] )


def flipflop(activate_trigger : Signal, disable_trigger : Signal, initial_state = False, nodelay = False):
    """
    Flipflop logic element

    The block has a state that can be activated or deactivated by the external boolean events 'activate_trigger'
    and 'disable_trigger', respectively.
    """
    
    return wrap_signal( Flipflop(dy.get_system_context(), activate_trigger.unwrap, disable_trigger.unwrap, initial_state = initial_state, nodelay=nodelay ).outputs[0] )




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
        return wrap_signal( Memory(dy.get_system_context(), datatype, constant_array, write_index.unwrap, value.unwrap).outputs[0] )
    elif write_index is None and value is None:
        return wrap_signal( Memory(dy.get_system_context(), datatype, constant_array).outputs[0] )
    else:
        raise BaseException('memory: write_index and value were not properly defined')

def memory_read( memory : SignalUserTemplate, index : SignalUserTemplate ):
    """
        Read an element from an array defined by memory()

        index - the index indicating the element to read.

        Returns the value of the element
    """
    return wrap_signal( MemoryRead(dy.get_system_context(), memory.unwrap, index.unwrap ).outputs[0] )
