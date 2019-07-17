
# from BlockPrototypes import Operator1

import BlockPrototypes as block_prototypes

from Signal import Signal, UndeterminedSignal, BlockOutputSignal, SimulationInputSignal


"""
    This adds a layer around the Signal-class and its derivates.
    It enhances the ease of use of signals by implementing operators
    inbetween signals e.g. it becomes possible to add, multiply, ...
    signal variables among each other.
"""

# TODO: This shall be the undetermined signal
class SignalUser(UndeterminedSignal):
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):

        UndeterminedSignal.__init__(self, sim)
    

    #
    # operator overloads
    #
    def __add__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals

    def __sub__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='-').outputSignals

    def __mul__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='*').outputSignals

    def __truediv__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='/').outputSignals

    def __lshift__(self, other): 
        # close a feedback loop by connecting the signals self and other        
        print("closing loop: " + self.getName() + ' <--> ' + other.getName() )
        self.setequal(other)
        
        return self


class BlockOutputSignalUser(BlockOutputSignal):
    """
        A signal that is the output of a block (normal case)
    """

    def __init__(self,  sim, datatype = None, sourceBlock = None, sourcePort = None):
        BlockOutputSignal.__init__(self, sim, datatype, sourceBlock, sourcePort)

    #
    # operator overloads
    #
    def __add__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals

    def __sub__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='-').outputSignals

    def __mul__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='*').outputSignals

    def __truediv__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='/').outputSignals

    # def __lshift__(self, other): 
    #     # close a feedback loop by connecting the signals self and other        
    #     print("closing loop: " + self.getName() + ' <--> ' + other.getName() )
    #     other.setequal(self)
        
        return self


class SimulationInputSignalUser(SimulationInputSignal):
    """
        A special signal that markes an input to a simulation.
    """

    def __init__(self, sim, datatype = None):
        SimulationInputSignal.__init__(self, sim, datatype=datatype)

    #
    # operator overloads
    #
    def __add__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals

    def __sub__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='-').outputSignals

    def __mul__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='*').outputSignals

    def __truediv__(self, other): 
        return block_prototypes.Operator1(self.sim, inputSignals=[ self, other ], operator='/').outputSignals

    # def __lshift__(self, other): 
    #     # close a feedback loop by connecting the signals self and other        
    #     print("closing loop: " + self.getName() + ' <--> ' + other.getName() )
    #     other.setequal(self)
        
        return self
