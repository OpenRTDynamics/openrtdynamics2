
# from BlockPrototypes import Operator1
from typing import Dict, List

import dynamics as dy
import BlockPrototypes as block_prototypes

from Signal import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal


"""
    This adds a layer around the Signal-class and its derivates.
    It enhances the ease of use of signals by implementing operators
    inbetween signals e.g. it becomes possible to add, multiply, ...
    signal variables among each other.
"""


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


    def setName(self, name):
        self.wrapped_signal_.setName(name)
        return self

    def extendName(self, name):
        self.wrapped_signal_.setName( self.wrapped_signal_.name + name )
        return self

    def setNameOfOrigin(self, name):
        self.wrapped_signal_.setNameOfOrigin(name)
        return self

    # ...

    #
    # operator overloads
    #
    def __add__(self, other): 
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='+').outputSignals )

    def __sub__(self, other): 
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='-').outputSignals )

    def __mul__(self, other): 
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='*').outputSignals )

    def __truediv__(self, other): 
        return wrap_signal( block_prototypes.Operator1( dy.get_simulation_context(), inputSignals=[ self.unwrap, other.unwrap ], operator='/').outputSignals )

    # comparison operators
    def __le__(self, other):
        return ( block_prototypes.comparison(left = self, right = other, operator = '<=' ) )

    def __ge__(self, other):
        return ( block_prototypes.comparison(left = self, right = other, operator = '>=' ) )


    def __lt__(self, other):
        return ( block_prototypes.comparison(left = self, right = other, operator = '<' ) )

    def __gt__(self, other):
        return ( block_prototypes.comparison(left = self, right = other, operator = '>' ) )


    def __eq__(self, other):
        return ( block_prototypes.comparison(left = self, right = other, operator = '==' ) )

    def __ne__(self, other):
        return ( block_prototypes.comparison(left = self, right = other, operator = '!=' ) )





# prev name was SignalUser, SignalUserAnonymous
class SignalUser(SignalUserTemplate):

    def __init__(self, sim):
        SignalUserTemplate.__init__( self, sim=sim, wrapped_signal=UndeterminedSignal(sim)  )

    def enherit_datatype(self, from_signal : SignalUserTemplate):
        """
            The datatype of this anonymous signal shall be inherited from the given signal 'from_signal'
        """
        # self.inherit_datatype_of_signal = from_signal

        # from_signal.unwrap.inherit_datatype_to( self.unwrap )

        self.unwrap.enherit_datatype_from_signal( from_signal.unwrap )



    # only ananymous signal
    def __lshift__(self, other): 
        # close a feedback loop by connecting the signals self and other        
        print("EDITOR: closing loop: " + self.name + ' <--> ' + other.name )
        self.unwrap.setequal(other.unwrap)
        
        return other





class SubsystemOutputLinkUser(SignalUser):
    """
        A signal that serves as a placeholder for a subsystem output to be used in the embedding
        system. A datatype must be specified.

        Signals of this kind are automatically generated during the compilation process when cutting the signals comming 
        from the subsystem blocks. 
    """

    def __init__(self, sim, original_signal : Signal):
        self._original_signal = original_signal

        SignalUser.__init__(self, sim)






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













# # TODO: This shall be the undetermined signal
# class SignalUser(UndeterminedSignal):
#     def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):

#         UndeterminedSignal.__init__(self, sim)
    

#     #
#     # operator overloads
#     #
#     def __add__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals

#     def __sub__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='-').outputSignals

#     def __mul__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='*').outputSignals

#     def __truediv__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='/').outputSignals

#     # comparison operators
#     def __le__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '<=' )

#     def __ge__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '>=' )


#     def __lt__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '<' )

#     def __gt__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '>' )


#     def __eq__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '==' )

#     def __ne__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '!=' )



#     def __lshift__(self, other): 
#         # close a feedback loop by connecting the signals self and other        
#         print("closing loop: " + self.getName() + ' <--> ' + other.getName() )
#         self.setequal(other)
        
#         return other


# class BlockOutputSignalUser(BlockOutputSignal):
#     """
#         A signal that is the output of a block (normal case)
#     """

#     def __init__(self,  sim, datatype = None, sourceBlock = None, sourcePort = None):
#         BlockOutputSignal.__init__(self, sim, datatype, sourceBlock, sourcePort)

#     #
#     # operator overloads
#     #
#     def __add__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals

#     def __sub__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='-').outputSignals

#     def __mul__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='*').outputSignals

#     def __truediv__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='/').outputSignals

#     # comparison operators
#     def __le__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '<=' )

#     def __ge__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '>=' )


#     def __lt__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '<' )

#     def __gt__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '>' )


#     def __eq__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '==' )

#     def __ne__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '!=' )

# class SimulationInputSignalUser(SimulationInputSignal):
#     """
#         A special signal that markes an input to a simulation.
#     """

#     def __init__(self, sim, datatype = None):
#         SimulationInputSignal.__init__(self, sim, datatype=datatype)

#     #
#     # operator overloads
#     #
#     def __add__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals

#     def __sub__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='-').outputSignals

#     def __mul__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='*').outputSignals

#     def __truediv__(self, other): 
#         return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='/').outputSignals

#     # comparison operators
#     def __le__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '<=' )

#     def __ge__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '>=' )


#     def __lt__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '<' )

#     def __gt__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '>' )


#     def __eq__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '==' )

#     def __ne__(self, other):
#         return block_prototypes.comparison(left = self, right = other, operator = '!=' )
