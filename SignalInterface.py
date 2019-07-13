from BlockPrototypes import *



class SignalUser(Signal):
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):

        Signal.__init__(self, sim, datatype=datatype, sourceBlock=sourceBlock, sourcePort=sourcePort )
    

    #
    # operator overloads
    #
    def __add__(self, other): 
        Operator1(self.sim, inputSignals=[ self, other ], operator='+').outputSignals


class BlockOutputSignalUser(BlockOutputSignal):
    """
        A signal that is the output of a block (normal case)

        TODO: implement and remove code from 'Signal' above
    """

    def __init__(self, sim, port : int, datatype = None):
        BlockOutputSignal.__init__(self, sim, port=port, datatype=datatype)



class SimulationInputSignalUser(SimulationInputSignal):
    """
        A special signal that markes an input to a simulation.
    """

    def __init__(self, sim, datatype = None):
        SimulationInputSignal.__init__(self, sim, datatype=datatype)
