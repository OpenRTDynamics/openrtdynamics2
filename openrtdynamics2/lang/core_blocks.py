from .block_prototypes import *
from .signal_interface import SignalUserTemplate, wrap_signal, wrap_signal_list, unwrap_hash, unwrap_list, unwrap
from . import system_context as dy
from .diagram_core import datatypes as dt

from typing import Dict, List


"""
    Core functions which directly point to blocks (implementation in, e.g., c++) 
"""


def generic_subsystem( manifest, inputSignals : List[SignalUserTemplate] ):
    return wrap_signal_list( GenericSubsystem(dy.get_current_system(), manifest, unwrap_hash(inputSignals) ).outputSignals )

def const(constant, datatype ):
    return wrap_signal( Const(dy.get_current_system(), constant, datatype).outputs[0] )

def gain(u : SignalUserTemplate, gain : float ):
    return wrap_signal( Gain(dy.get_current_system(), u.unwrap, gain).outputs[0] )

def convert(u : SignalUserTemplate, target_type : dt.DataType ):
    """
    Datatype conversion

    The input is converted to the given datatype

    Parameters
    ----------
    u : SignalUserTemplate
        the input signal
    target_type
        the datatype to convert the signal to

    Returns
    -------
    SignalUserTemplate
        the output signal with the given type
    """
    return wrap_signal( ConvertDatatype(dy.get_current_system(), u.unwrap, target_type).outputs[0] )

def add(input_signals : List[SignalUserTemplate], factors : List[float]):
    """
    Linear combination of the list of input signals with the list of factors

    the output is given by

        input_signals[0] * factors[0] + input_signals[1] * factors[1] + ...
    """
    return wrap_signal( Add(dy.get_current_system(), unwrap_list( input_signals ), factors).outputs[0] )

def operator1(inputSignals : List[SignalUserTemplate], operator : str ):
    return wrap_signal( Operator1(dy.get_current_system(), unwrap_list( inputSignals ), operator).outputs[0] )


#
# logic operators
#

def logic_and(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        logical and

        u1 && u2
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list([u1,u2]), operator=' && ').outputs[0] )

def logic_or(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        logical or
    
        u1 || u2
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list( [u1,u2] ), operator=' || ').outputs[0] )


def logic_xor(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        exclusive logical or (xor)
    
        u1 ^ u2
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list( [u1,u2] ), operator=' ^ ').outputs[0] )


def bitwise_and(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        bitwise and

        u1 & u2
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list([u1,u2]), operator=' & ').outputs[0] )

def bitwise_or(u1 : SignalUserTemplate, u2 : SignalUserTemplate):
    """
        bitwise or
    
        u1 | u2
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list( [u1,u2] ), operator=' | ').outputs[0] )


def bitwise_shift_left(u : SignalUserTemplate, shift : SignalUserTemplate):
    """
        logical shift left
    
        u << shift
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list( [u,shift] ), operator=' << ').outputs[0] )


def bitwise_shift_right(u : SignalUserTemplate, shift : SignalUserTemplate):
    """
        logical shift left
    
        u >> shift
    """

    return wrap_signal( Operator1(dy.get_current_system(), inputSignals=unwrap_list( [u,shift] ), operator=' >> ').outputs[0] )









def comparison(left : SignalUserTemplate, right : SignalUserTemplate, operator : str ):
    return wrap_signal( ComparisionOperator(dy.get_current_system(), left.unwrap, right.unwrap, operator).outputs[0] )

def switchNto1( state : SignalUserTemplate, inputs : List[SignalUserTemplate] ):
    """N to one signal switch

    returns 

        inputs[0]  for state == 1
        inputs[1]  for state == 2
        inputs[2]  for state == 3
           ...

    Parameters
    ----------
    state : SignalUserTemplate
        the state of the switch  
    inputs : List[SignalUserTemplate]
        the input signals among which to switch

    Returns
    -------
    SignalUserTemplate
        the output signal of the switch
    """
    return wrap_signal( SwitchNto1(dy.get_current_system(), state.unwrap, unwrap_list(inputs) ).outputs[0] )

def conditional_overwrite(signal : SignalUserTemplate, condition : SignalUserTemplate, new_value ):
    """
    Overwrite the input signal by a given value in case a condition is true

    The output is given by

        signal     for condition==false
        new_value  for condition==true

    Parameters
    ----------
    signal : SignalUserTemplate
        the input signal
    condition : SignalUserTemplate
        the boolean condition for when to overwrite signal
    new_value : SignalUserTemplate, float, int
        the value with is used to replace the input in case the condition is true

    Returns
    -------
    SignalUserTemplate
        the output signal
    """

    if isinstance(new_value, SignalUserTemplate):
        new_value = new_value.unwrap

    return wrap_signal( ConditionalOverwrite(dy.get_current_system(), signal.unwrap, condition.unwrap, new_value).outputs[0] )

def if_else(condition : SignalUserTemplate, if_true : SignalUserTemplate, if_false : SignalUserTemplate  ):
    """
    IF/ELSE - select one of two input signals given a condition

    The output is given by

        if_true     for condition==true
        if_false    for condition==false

    Parameters
    ----------
    condition : SignalUserTemplate
        the boolean condition for when to overwrite signal
    if_true : SignalUserTemplate
        the input signal
    if_false : SignalUserTemplate
        the value with is used to replace the input in case the condition is true

    Returns
    -------
    SignalUserTemplate
        the output signal
    """

    return wrap_signal( 
            ConditionalOverwrite(
                dy.get_current_system(), 
                if_false.unwrap, 
                condition.unwrap, 
                if_true.unwrap
            ).outputs[0] 
        )



def sqrt(u : SignalUserTemplate ):
    """
    Square root
    """
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'sqrt').outputs[0] )

def sin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'sin').outputs[0] )

def cos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'cos').outputs[0] )

def tan(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'tan').outputs[0] )

def atan(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'atan').outputs[0] )

def asin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'asin').outputs[0] )

def acos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'acos').outputs[0] )

def abs(u : SignalUserTemplate ):
    """
    Absolute value

    Computes the absolute value |u|.
    """
    return wrap_signal( StaticFnByName_1To1(dy.get_current_system(), u.unwrap, 'abs').outputs[0] )



def logic_not(u : SignalUserTemplate ):
    """
    Logic negation

    Parameters
    ----------
    u : SignalUserTemplate
        the boolean input signal

    Returns
    -------
    SignalUserTemplate
        the boolean output signal

    Details
    -------
    returns 
        !u
    """
    return wrap_signal( Operator0(dy.get_current_system(), u.unwrap, '!').outputs[0] )

def bitwise_not(u : SignalUserTemplate ):
    """
    Bitwise not operator

    Parameters
    ----------
    u : SignalUserTemplate
        the integer input signal

    Returns
    -------
    SignalUserTemplate
        the integer output signal

    Details
    -------
    returns 
        ~u
    """
    return wrap_signal( Operator0(dy.get_current_system(), u.unwrap, '~').outputs[0] )


def atan2(y : SignalUserTemplate, x : SignalUserTemplate ):
    """
        atan2

        This function returns atan2(x,y).

        Parameters
        ----------
        x : SignalUserTemplate
            x
        y : SignalUserTemplate
            y

        Returns
        -------
        SignalUserTemplate
            the output signal

        Details
        -------
        returns 
            atan2(x,y)

    """
    return wrap_signal( StaticFnByName_2To1(dy.get_current_system(), y.unwrap, x.unwrap, 'atan2').outputs[0] )

def pow(x : SignalUserTemplate, y : SignalUserTemplate ):
    """
        Power function for floating point values

        This function returns the x to the power of y (x^y).

        Parameters
        ----------
        x : SignalUserTemplate
            x
        y : SignalUserTemplate
            y

        Returns
        -------
        SignalUserTemplate
            the output signal

        Details
        -------
            returns pow(x,y)

    """
    return wrap_signal( StaticFnByName_2To1(dy.get_current_system(), x.unwrap, y.unwrap, 'pow').outputs[0] )

def fmod(x : SignalUserTemplate, y : SignalUserTemplate ):
    """
        Modulo function for floating point values

        This function returns the remainder of dividing x/y.

        Parameters
        ----------
        x : SignalUserTemplate
            x
        y : SignalUserTemplate
            y

        Returns
        -------
        SignalUserTemplate
            the output signal

        Details
        -------
            returns fmod(x,y)

    """
    return wrap_signal( StaticFnByName_2To1(dy.get_current_system(), x.unwrap, y.unwrap, 'fmod').outputs[0] )







def cpp_allocate_class(datatype, code_constructor_call):
    """
        Return a pointer signal pointing to a class instance initialized by code_constructor_call

        Parameters
        ----------
        ptr_signal : DataTypePointer
            the datatype of the pointer to use
        code_constructor_call : str
            the code to initialize the class instance

    """
    return wrap_signal( AllocateClass(dy.get_current_system(), datatype, code_constructor_call).outputs[0] )



def cpp_call_class_member_function(
    ptr_signal : SignalUserTemplate, 
        
    input_signals : List[SignalUserTemplate], input_types, 
    output_types,

    member_function_name_to_calc_outputs : str = None,
    member_function_name_to_update_states : str = None,
    member_function_name_to_reset_states : str = None

):
    """
        Call member functions of a c++ class

        This function calls member functions of a class instance given by a pointer to an instance.
        In- and outputs are passed as parameters to the member function given by
        'member_function_name_to_calc_outputs'. Herein, the output signals are the first parameters
        and the input signals then follow.

        On an optional state update call, the member function 'member_function_name_to_update_states'
        is called and the parameters are the input signals.

        Parameters
        ----------
        ptr_signal : SignalUserTemplate
            the pointer to the class instance as generated by cpp_allocate_class()
        input_signals : SignalUserTemplate
            a list of input signals that are passed to the called member functions via the parameters
        input_types : List[ Datatype ]
            the datatypes of the inputs
        output_types : List[ Datatype ]
            the datatypes of the outputs
        member_function_name_to_calc_outputs : str
            the name of the member function to call to compute the output signals
        member_function_name_to_update_states : str
            optional: the name of the member function to call to update the states

        Returns
        -------
        List[SignalUserTemplate|
            the output signals

    """
    bp = CallClassMemberFunction(
        dy.get_current_system(), 
        unwrap_list(input_signals), 
        input_types, 
        output_types, 
        ptr_signal = ptr_signal.unwrap,

        member_function_name_to_calc_outputs  = member_function_name_to_calc_outputs,
        member_function_name_to_update_states = member_function_name_to_update_states,
        member_function_name_to_reset_states  = member_function_name_to_reset_states
    )
    return wrap_signal_list( bp.outputs )



def generic_cpp_static(
    input_signals : List[SignalUserTemplate], input_names : List [str], input_types, 
    output_names, output_types, 
    cpp_source_code : str
):
    """
    Embed C/C++ source code (stateless code only)

    Parameters
    ----------
    input_signals : List[SignalUserTemplate]
        the list of input signals
    input_names : List[str]
        the list of the names of the input signals to be used as variable names for the c++ code
    input_types : List[Datatype]
        the list of the datatypes of the input signals (must be fixed)
    output_types : List[Datatype]
        the list of the datatypes of the output signals (must be fixed)
    output_names : List[str]
        the list of the names of the output signals to be used as variable names for the c++ code
    cpp_source_code : str
        the code to embed

    Returns
    -------
    List[SignalUserTemplate]
        the output signals

    Example
    -------

        source_code = \"\"\"

            // This is c++ code
            output1 = value;
            if (someinput > value) {
                output2 = value;
            } else {
                output2 = someinput;
            }
            output3 = 0.0;

        \"\"\"

        outputs = dy.generic_cpp_static(
            input_signals=[ someinput, value ], input_names=[ 'someinput', 'value' ], 
            input_types=[ dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ], 
            output_names=['output1', 'output2', 'output3'],
            output_types=[ dy.DataTypeFloat64(1), dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ],
            cpp_source_code = source_code
        )

        output1 = outputs[0]
        output2 = outputs[1]
        output3 = outputs[2]
    """
    return wrap_signal_list( GenericCppStatic(dy.get_current_system(), unwrap_list(input_signals), input_names, input_types, output_names, output_types, cpp_source_code  ).outputs )

def delay__(u : SignalUserTemplate, initial_state = None):
    return wrap_signal( Delay(dy.get_current_system(), u.unwrap, initial_state ).outputs[0] )


def flipflop(activate_trigger : SignalUserTemplate, disable_trigger : SignalUserTemplate, initial_state = False, no_delay = False):
    """Flipflop logic element

    The block has a state that can be activated or deactivated by the external boolean events 'activate_trigger'
    and 'disable_trigger', respectively.

    Parameters
    ----------
    activate_trigger : SignalUserTemplate       
        the event to activate the state
    disable_trigger : SignalUserTemplate       
        the event to deactivate the state
    initial_state : bool       
        the initial state
    no_delay : bool
        return the state change without a delay 

    Returns
    -------
    SignalUserTemplate
        the state

    """
    
    return wrap_signal( Flipflop(dy.get_current_system(), activate_trigger.unwrap, disable_trigger.unwrap, initial_state = initial_state, no_delay=no_delay ).outputs[0] )




def memory(datatype, constant_array, write_index : SignalUserTemplate = None, value : SignalUserTemplate = None):
    """
    Define an array for storing and reading values

    Allocates static memory for an array of elements given a datatype.
    During each sampling instant, one element can be (over)written. 

    Parameters
    ----------
    datatype : Datatype       
        the datatype of the array elements
    constant_array : List[float], List[int]
        list of constants that contain the data to initialize the array
    write_index : SignalUserTemplate
        the array index (integer signal) of the element to replace by value (optional)
    value : SignalUserTemplate
        the value to write into the array at write_index (optional)

    returns a reference to the memory segment which is accessible by memory_read()

    Returns
    -------
    List[SignalUserTemplate]
        a reference to the memory segment which is accessible by memory_read()


    Limitations
    -----------
    currently the memory is not reset on subsystem reset. This will change.
    """

    if write_index is not None and value is not None:
        return wrap_signal( Memory(dy.get_current_system(), datatype, constant_array, write_index.unwrap, value.unwrap).outputs[0] )
    elif write_index is None and value is None:
        return wrap_signal( Memory(dy.get_current_system(), datatype, constant_array).outputs[0] )
    else:
        raise BaseException('memory: write_index and value were not properly defined')

def memory_read( memory : SignalUserTemplate, index : SignalUserTemplate ):
    """
    Read an element from an array defined by memory()

    Parameters
    ----------
    memory : SignalUserTemplate
        the memory as returned by memory()
    index : SignalUserTemplate
        the index indicating the element to read

    Returns
    -------
    List[SignalUserTemplate]
        returns the value of the element
    """
    return wrap_signal( MemoryRead(dy.get_current_system(), memory.unwrap, index.unwrap ).outputs[0] )
