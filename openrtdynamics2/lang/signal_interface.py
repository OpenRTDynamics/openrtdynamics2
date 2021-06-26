from . import lang as dy
from . import block_prototypes as block_prototypes
from .diagram_core.signal_network.signals import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal

from typing import Dict, List

"""
    This adds a layer around the signal-class.
    It enhances the ease of use of signals by implementing operators
    in-between signals e.g. it becomes possible to add, multiply, ...
    signal variables among each other.
"""


class structure:
    """
    A structure to combine multiple signals
    
    It behaves similarly to a python hash array.
    Further, the keys are used as (part of) the variable names in the generated code. 
    """
    def __init__(self, *args, **kwargs):
        
        if len(args) == 1:
            self._entries = args[0]
        else:
            self._entries = kwargs
        
        # list of signals; deterministic order
        self._signals = []
        self._keys    = []
        
        for k, s in self._entries.items():
            s.set_name( k )
            self._signals.append(s)
            self._keys.append(k)
        
    def __getitem__(self, key):
        return self._entries[key]

    def __setitem__(self, key, signal):
        signal.set_name( key )
        
        self._entries[key] = signal
        self._signals.append(signal)
        self._keys.append(key)

    def items(self):
        """
        items function - like a hash array has
        """
        return self._entries.items()
    
    def to_list(self):
        """
        return an ordered list of the signals stored in this structure
        """
        return self._signals
    
    def replace_signals(self, signals):
        """
        replace the signals stored in this structure with the given list of signals. 
        The given list shall have the same order like the list returned by to_list(). 
        """
        
        for i in range(0, len(signals)):
            s = signals[i]
            k = self._keys[i]
            
            self._entries[k] = s
            
        self._signals = signals
            
            


def convert_python_constant_val_to_const_signal(val):

    if isinstance(val, SignalUserTemplate):
        # given value is already a signal
        return val

    if type(val) == int:  # TODO: check for range and eventually make int64
        return dy.int32(val)

    if type(val) == float:
        return dy.float64(val)

    raise BaseException('unable to convert given source ' + str(val) + ' to a signal object.')


# internal helper
def _comparison(left, right, operator : str ):
    return wrap_signal( block_prototypes.ComparisionOperator(dy.get_current_system(), left.unwrap, right.unwrap, operator).outputs[0] )


class SignalUserTemplate(object):
    def __init__(self, system, wrapped_signal : Signal):

        self._system = system
        self._wrapped_signal = wrapped_signal

    def __hash__(self):
        return id(self)

    @property
    def unwrap(self):
        """
        Get the library-internal representation of a signal (internal use only)
        """
        return self._wrapped_signal

    @property
    def name(self):
        """
        the identifier of the signal
        """
        return self._wrapped_signal.name

    @property
    def properties(self):
        """
        A hash array of properties describing the signal
        """
        return self._wrapped_signal.properties

    def set_properties(self, p):
        """
        Set the properties of the signal
        """
        self._wrapped_signal.properties = { **self._wrapped_signal.properties, **p }
        return self

    def set_datatype(self, datatype):
        # call setDatatype_nonotitication to prevent the (untested) automatic update of the datatypes
        self._wrapped_signal.setDatatype_nonotitication(datatype)
        return self

    def set_name(self, name):
        """
        Set the signals identifier. Must be a string without spaces and alphanumerical characters only. 
        """
        self._wrapped_signal.set_name(name)
        return self

    # TODO: can this be removed?
    def set_name_raw(self, name):
        self._wrapped_signal.set_name_raw(name)
        return self


    def extend_name(self, name):
        """
        Extend the current signal identifier by appending characters at the end of the string
        """
        self._wrapped_signal.set_name( self._wrapped_signal.name + name )
        return self

    def set_blockname(self, name):
        """
        Set the name of the block that has the signal as one of its outputs
        """
        self._wrapped_signal.set_blockname(name)
        return self

    # ...

    #
    # operator overloads
    #

    def __add__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ self.unwrap, other.unwrap ], operator='+').outputs[0] )

    def __radd__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ self.unwrap, other.unwrap ], operator='+').outputs[0] )


    def __sub__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ self.unwrap, other.unwrap ], operator='-').outputs[0] )

    def __rsub__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ other.unwrap, self.unwrap ], operator='-').outputs[0] )


    def __mul__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ self.unwrap, other.unwrap ], operator='*').outputs[0] )

    def __rmul__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ self.unwrap, other.unwrap ], operator='*').outputs[0] )


    def __truediv__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ self.unwrap, other.unwrap ], operator='/').outputs[0] )

    def __rtruediv__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_current_system(), inputSignals=[ other.unwrap, self.unwrap ], operator='/').outputs[0] )



    # _comparison operators
    def __le__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '<=' ) )

    def __rle__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = other, right = self, operator = '<=' ) )



    def __ge__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '>=' ) )

    def __rge__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = other, right = self, operator = '>=' ) )



    def __lt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '<' ) )

    def __rlt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = other, right = self, operator = '<' ) )



    def __gt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '>' ) )

    def __rgt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = other, right = self, operator = '>' ) )



    def __eq__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '==' ) )

    def __req__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '==' ) )

    def __ne__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '!=' ) )

    def __rne__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( _comparison(left = self, right = other, operator = '!=' ) )




# prev name was SignalUser, SignalUserAnonymous
class SignalUser(SignalUserTemplate):

    def __init__(self, sim):
        SignalUserTemplate.__init__( self, system=sim, wrapped_signal=UndeterminedSignal(sim)  )

    def inherit_datatype(self, from_signal : SignalUserTemplate):
        """
            The datatype of this anonymous signal shall be inherited from the given signal 'from_signal'
        """
        # self.inherit_datatype_of_signal = from_signal

        # from_signal.unwrap.inherit_datatype_to( self.unwrap )

        self.unwrap.inherit_datatype_from_signal( from_signal.unwrap )



    # only for anonymous (feedback) signals
    def __lshift__(self, other): 
        # close a feedback loop by connecting the signals self and other        
        self.unwrap.setequal(other.unwrap)
        
        return other







class BlockOutputSignalUser(SignalUserTemplate):
    """
        A signal that is the output of a block (normal case)
    """

    def __init__(self, signalToWrap : BlockOutputSignal):
        SignalUserTemplate.__init__( self, system=signalToWrap.system, wrapped_signal=signalToWrap  )







class SimulationInputSignalUser(SignalUserTemplate):
    """
        A special signal that is an input to a simulation.
    """

    def __init__(self, system, datatype = None):

        input_signal = SimulationInputSignal(system, datatype=datatype)
        SignalUserTemplate.__init__( self, system=system, wrapped_signal=input_signal  )






def unwrap( signal : SignalUserTemplate ):
    return signal.unwrap

def unwrap_list( signals : List[SignalUserTemplate] ):

    # create a new list of signals
    list_of_unwrapped_signals=[]
    for signal in signals:
        list_of_unwrapped_signals.append( signal.unwrap )

    return list_of_unwrapped_signals 

def unwrap_hash( signals ):
    """
        unwrap all signals in a hash array and return a copy 
    """

    # make a copy
    list_of_unwrapped_signals = signals.copy()

    # create a new list of signals
    for key, signal in list_of_unwrapped_signals.items():
        list_of_unwrapped_signals[key] = signal.unwrap

    return list_of_unwrapped_signals 


def wrap_signal( signal : Signal ):
    # wraps a block output signal
    return BlockOutputSignalUser( signal )


def wrap_signal_list( signals : List[ Signal ] ):
    # wraps a list of block output signals
    list_of_wrapped_signals=[]
    for signal in signals:
        list_of_wrapped_signals.append( BlockOutputSignalUser( signal ) )

    return list_of_wrapped_signals

