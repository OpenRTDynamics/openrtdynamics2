from typing import Dict, List

from Signal import *
from Datatypes import *





class Block:
    """
        This decribes a block that is part of a Simulation
     
        BlockPrototype - describes the block's prototype implementation
                         that defined IO, parameters, ...
        inputSignal    - list of input signals serving as the inputs to the block (might be set later
                         by update_input_config() )
        blockname      - A string name of the block (default '')
    """

    def __init__(self, sim, blockPrototype, inputSignals : List[Signal] = None, blockname : str = ''):
        # print("Creating new block " + blockname)

        self.sim = sim

        # create a new unique block id 
        self._id = sim.getNewBlockId()

        # default names
        if blockname is None:
            blockname = ''

        self.blocknameShort =  blockname + '_bid' + str( self._id )   # variable name
        self.blockname = blockname + '_bid' + str( self._id )  # description

        # add myself to the given simulation
        self.sim.addBlock(self)

        # The blocks prototype function. e.g. to determine the port sizes and types
        # and to define the parameters
        self.blockPrototype = blockPrototype

        # The input singals in form of a list
        self.inputSignals = None

        if inputSignals is not None:
            # store the list of input signals
            self.inputSignals = inputSignals # array of Signal

            # update the input signals to also point to this block
            for port in range(0, len( self.inputSignals ) ):
                self.inputSignals[port].addDestination( self, port )


        # initialize the empty list of output signals
        self.OutputSignals = []

        # used by TraverseGraph as a helper variable to perform a marking of the graph nodes
        self.graphTraversionMarker = False

    def update_input_config(self, input_signals):
        """
            Set the input signals after creation of the block (only if they were not set on
            construction)
        """
        if self.inputSignals is not None:
            raise BaseException("Input signals are already defined")

        self.inputSignals = input_signals



    def graphTraversionMarkerReset(self):
        self.graphTraversionMarker = False

    def graphTraversionMarkerMarkVisited(self):
        self.graphTraversionMarker = True
    
    def graphTraversionMarkerMarkIsVisited(self):
        return self.graphTraversionMarker

    def configOutputSignals(self, signals):
        self.OutputSignals = signals

    def verifyInputSignals(self, ignore_signals_with_datatype_inheritance = False):
        # check the input signals for proper connections to other blocks or simulation inputs
        # i.e. replace all anonymous signals with the sources
        resolveUndeterminedSignals( self.inputSignals, ignore_signals_with_datatype_inheritance )


    def configDefineOutputTypes(self):
        # ask the block's prototype class instance to define the output types given
        # the input types by calling the prototype's function 'configDefineOutputTypes' 
        # 
        # Please note that the input types are define by other blocks
        # whose outputs are connected to this block.
        #
        # It might happen that the datatypes of these signals are not already determined.
        # Eventually a proposal for a datatype is available. In any case, based on the available
        # information, the prototype is asked to provide information on the types of the outputs.
        #


        # build a list of input signals types for this block
        inputSignalTypes = []

        for s in self.inputSignals:

            if s.getDatatype() is not None:
                # this input's datatype is already fixed 
                inputSignalTypes.append(s.getDatatype() )
            else:
                # check for the proposed datatype
                if s.getProposedDatatype() is not None:
                    inputSignalTypes.append(s.getProposedDatatype() )
                else:
                    # no info on this input signal is available -- just put None and let the blocks propotype
                    # 'configDefineOutputTypes' function deceide what to do.
                    inputSignalTypes.append(None)


        # ask prototype to define output types (this might just be a proposal for datatypes; they are fixed later)
        proposedOutputSingalTypes = self.blockPrototype.configDefineOutputTypes( inputSignalTypes )

        # update all signals accordingly
        for i in range(0, len(self.OutputSignals)):

            signal = self.OutputSignals[i]
            signal.setProposedDatatype(  proposedOutputSingalTypes[i]  )

        return


    def getName(self):
        return self.blocknameShort

    def setName(self, name):
        self.blockname = name
        return self

    def toStr(self):
        return self.blockname + ' (' + self.blocknameShort + ')'

    def getBlockPrototype(self):
        return self.blockPrototype

    def getBlockId(self):
        return self._id # a unique id within the simulation the block is part of

    @property
    def id(self):
        return self._id


    def getInputSignals(self):
        return self.inputSignals

    @property 
    def inputs(self):
        return self.inputSignals

    def getOutputSignals(self):
        return self.OutputSignals

    def getOutputSignal(self, port):
        if port < 0:
            raise Exception('port < 0')

        if port >= len(self.OutputSignals): 
            raise Exception('port out of range')

        return self.OutputSignals[port]

    def getInputSignal(self, port):
        if port < 0:
            raise Exception('port < 0')

        if port >= len(self.inputSignals): 
            raise Exception('port out of range')

        return self.inputSignals[port]
    













