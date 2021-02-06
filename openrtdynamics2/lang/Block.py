from typing import Dict, List

from .signals import *
from .datatypes import *

import random as random



class Block:
    """
        This decribes a block that is part of a Simulation
     
        BlockPrototype - describes the block's prototype implementation
                         that defined IO, parameters, ...
        inputSignal    - list of input signals serving as the inputs to the block (might be set later
                         by update_input_config() )
        blockname      - A string name of the block (default '')
    """

    def __init__(self, sim, blockPrototype, inputSignals : List[Signal] = None, blockname : str = None):

        self.sim = sim

        # create a new unique block id (unique for the system the block is in)
 #       self._id = random.randint(0,1000000) + sim.getNewBlockId()
        self._id = sim.getNewBlockId()

        # default names
        if blockname is None:
            self.blockname = str( self._id )
        else:
            self.blockname = blockname

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

        # used by graph_traversion as a helper variable to perform a marking of the graph nodes
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


    def config_request_define_output_types(self):
        # ask the block's prototype class instance to define the output types given
        # the input types by calling the prototype's function 'config_request_define_output_types' 
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
                    # 'config_request_define_output_types' function deceide what to do.
                    inputSignalTypes.append(None)


        # ask prototype to define output types (this might just be a proposal for datatypes; they are fixed later)
        proposedOutputSingalTypes = self.blockPrototype.config_request_define_output_types( inputSignalTypes )

        # update all signals accordingly
        for i in range(0, len(self.OutputSignals)):

            if proposedOutputSingalTypes[i] is not None:
                signal = self.OutputSignals[i]
                signal.setProposedDatatype(  proposedOutputSingalTypes[i]  )

        return


    def getName(self):
        return self.blockname

    @property
    def name(self):
        return self.blockname

    def set_name(self, name):
        self.blockname = name
        return self

    def toStr(self):
        return self.blockname

    def getBlockPrototype(self):
        return self.blockPrototype

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














