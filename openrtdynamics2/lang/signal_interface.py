from typing import Dict, List

from . import lang as dy
from . import block_prototypes as block_prototypes

from .signals import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal


"""
    This adds a layer around the signal-class.
    It enhances the ease of use of signals by implementing operators
    in-between signals e.g. it becomes possible to add, multiply, ...
    signal variables among each other.
"""


def convert_python_constant_val_to_const_signal(val):

    if isinstance(val, SignalUserTemplate):
        # given value is already a signal
        return val

    if type(val) == int:  # TODO: check for range and eventually make int64
        return dy.int32(val)

    if type(val) == float:
        return dy.float64(val)

    raise BaseException('unable to convert given constant ' + str(val) + ' to a signal object.')


class SignalUserTemplate(object):
    def __init__(self, sim, wrapped_signal : Signal):

        self.sim = sim
        self.wrapped_signal_ = wrapped_signal

    def __hash__(self):
        return id(self)

    @property
    def unwrap(self):
        return self.wrapped_signal_

    @property
    def name(self):
        return self.wrapped_signal_.name

    @property
    def properties(self):
        return self.wrapped_signal_.properties

    def set_properties(self, p):
        self.wrapped_signal_.set_properties(p)
        return self

    def set_datatype(self, datatype):
        # call setDatatype_nonotitication to prevent the (untested) automatic update of the datatypes
        self.wrapped_signal_.setDatatype_nonotitication(datatype)
        return self

    def set_name(self, name):
        self.wrapped_signal_.set_name(name)
        return self

    def set_name_raw(self, name):
        self.wrapped_signal_.set_name_raw(name)
        return self


    def extendName(self, name):
        self.wrapped_signal_.set_name( self.wrapped_signal_.name + name )
        return self

    def set_blockname(self, name):
        self.wrapped_signal_.set_blockname(name)
        return self

    # ...

    #
    # operator overloads
    #

    def __add__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='+').outputs[0] )

    def __radd__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='+').outputs[0] )


    def __sub__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='-').outputs[0] )

    def __rsub__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ other.unwrap, self.unwrap ], operator='-').outputs[0] )


    def __mul__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='*').outputs[0] )

    def __rmul__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='*').outputs[0] )


    def __truediv__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='/').outputs[0] )

    def __rtruediv__(self, other): 
        other = convert_python_constant_val_to_const_signal(other)
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ other.unwrap, self.unwrap ], operator='/').outputs[0] )


    # comparison operators
    def __le__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '<=' ) )

    def __rle__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = other, right = self, operator = '<=' ) )



    def __ge__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '>=' ) )

    def __rge__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = other, right = self, operator = '>=' ) )



    def __lt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '<' ) )

    def __rlt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = other, right = self, operator = '<' ) )



    def __gt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '>' ) )

    def __rgt__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = other, right = self, operator = '>' ) )



    def __eq__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '==' ) )

    def __req__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '==' ) )

    def __ne__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '!=' ) )

    def __rne__(self, other):
        other = convert_python_constant_val_to_const_signal(other)
        return ( block_prototypes.comparison(left = self, right = other, operator = '!=' ) )




# prev name was SignalUser, SignalUserAnonymous
class SignalUser(SignalUserTemplate):

    def __init__(self, sim):
        SignalUserTemplate.__init__( self, sim=sim, wrapped_signal=UndeterminedSignal(sim)  )

    def inherit_datatype(self, from_signal : SignalUserTemplate):
        """
            The datatype of this anonymous signal shall be inherited from the given signal 'from_signal'
        """
        # self.inherit_datatype_of_signal = from_signal

        # from_signal.unwrap.inherit_datatype_to( self.unwrap )

        self.unwrap.inherit_datatype_from_signal( from_signal.unwrap )



    # only ananymous signal
    def __lshift__(self, other): 
        # close a feedback loop by connecting the signals self and other        
        self.unwrap.setequal(other.unwrap)
        
        return other




# #
# # TODO: is this still needed?
# #
# class SubsystemOutputLinkUser(SignalUser):
#     """
#         A signal that serves as a placeholder for a subsystem output to be used in the embedding
#         system. A datatype must be specified.

#         Signals of this kind are automatically generated during the compilation process when cutting the signals comming 
#         from the subsystem blocks. 
#     """

#     def __init__(self, sim, original_signal : Signal):
#         self._original_signal = original_signal

#         SignalUser.__init__(self, sim)






class BlockOutputSignalUser(SignalUserTemplate):
    """
        A signal that is the output of a block (normal case)
    """

    def __init__(self, signalToWrap : BlockOutputSignal):
        SignalUserTemplate.__init__( self, sim=signalToWrap.system, wrapped_signal=signalToWrap  )







class SimulationInputSignalUser(SignalUserTemplate):
    """
        A special signal that markes an input to a simulation.
    """

    def __init__(self, sim, datatype = None):
        SignalUserTemplate.__init__( self, sim=sim, wrapped_signal=SimulationInputSignal(sim, datatype=datatype)  )






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

