from typing import Dict, List

from Signal import *






class DataType:
    #
    # TODO: feature: add type of datype: 1) 'C++', 'ORTD (old)', 'ORTD (V2)' + optional 'is reference flag' 
    #
    #
    #
    #



    def __init__(self, type : int, size : int):
        self.type = type
        self.size = size

    def isEqualTo(self, otherType):
        # output types
        # -1 undefined, 1 equal types, 0 type missmatch

        #print("DataType:isEqualTo " + str(self.size) + "==" + str(otherType.size) + " -- " + str(self.type) + " == " + str(otherType.type) )
        if otherType is None:
            return -1

        if not self.isDefined():
            return -1

        if not otherType.isDefined():
            return -1

        if self.size == otherType.size and self.type == otherType.type:
            return 1
        else:
            return 0

    def isDefined(self):
        if self.type is None:
            return False

        if self.size is None:
            return False

        return True

    def show(self):
        print("Datatype: type=" + str(self.type) + " size=" + str(self.size) )

    def toStr(self):
        return "type=" + str(self.type) + " size=" + str(self.size)




class InputDefinitions:
    # This defines a list of datatypes for each input port
    # if the input type of one port is undecided
    # the list element is None
    def __init__( self, ports : List[ DataType ]  ):

        self.ports = ports

    def getNPorts(self):
        return len( self.ports )

    def getType(self, port : int):
        return self.ports[port]


class OutputDefinitions:
    # This defines a list of datatypes for each output port
    # if the output type of one port is undecided
    # the list element is None
    def __init__( self, ports : List[ DataType ]  ):

        self.ports = ports

    def getNPorts(self):
        return len( self.ports )

    def getType(self, port : int):
        return self.ports[port]






############################

    # create new block with the inputs in inlist

    # -- Just store which type of subsimulation block to create:
    #
    # if / for / ...
    #
    # and then do later during export of the schematic
    #
    # In general, think about something to store an abstract representation of each block
    # and do all the work of parameter creation on export
    #
    # Maybe use classes for each block, instead of functions (def:)
    # class functions could be __init__ (collect parameters), check IO, export()
    #
    #
    # (This way, different backends can be supported)
    #






class BlockPrototype:
    # This is a base class to be deviated from each block type.
    # It contains logic to handle the input/ output types and
    # the parameters.
    # In future, also the implementation might go into it



    def __init__(self, block):
        self.block = block


    def defineOutputTypes(self):
        pass
    
    def getOutputTypes(self):
        # shall return OutTypes : OutputDefinitions

        pass

    def exportSetting(self):
        # maybe in case of a new interpreter
        pass

    def GetOutputsSingnals(self):
        pass

    def encode_irpar(self):
        # in case of traditional ORTD

        ipar = []
        rpar = []

        return ipar, rpar


    def getORTD_btype(self):
        pass
    
    def generateCode(self):
        pass

    #
    # TODO: 28.4.19: use these shortcuts to access the I/O signals
    #

    # get a signal of a specific output port
    def outputSignal(self, port):
        #return self.block.getOutputSignals()[port]
        return self.block.GetOutputSignal(port)

    # get a signal of a specific input port
    def inputSignal(self, port):
        return self.block.GetInputSignal(port)











# TODO: 15.3.19 : The block class should not store any informatino about the input/output signal types
# this info shall just be stored in the signal structures (DONE for the output signals)

class Block:
    # This decribes a block that is part of a Simulation
    # 
    # BlockPrototype - describes the block's prototype implementation
    #                  that defined IO, parameters, ...

    def __init__(self, sim, blockPrototype : BlockPrototype, inputSignals : List[Signal], blockname : str):
        print("Creating new block " + blockname)

        self.sim = sim
        self.blockname = blockname

        # add myself to the given simulation
        self.sim.addBlock(self)

        #operator, blocktype



        # The blocks prototype function. e.g. to determine the port sizes and types
        # and to define the parameters
        self.blockPrototype = blockPrototype

        # The input singals in form of a list
        self.inputSignals = []

        if not inputSignals is None:
            # store the list of input signals
            self.inputSignals = inputSignals # array of Signal

            # update the input signals to also point to this block
            for port in range(0, len( self.inputSignals ) ):
                self.inputSignals[port].addDestination( self, port )


        # create a new unique block id 
        self.id = sim.getNewBlockId()

        # initialize the empty list of output signals
        self.OutputSignals = []

        # get new block id (This is for the old ORTD-Style)
        self.id = sim.getNewBlockId()

        # used by TraverseGraph as a helper variable to perform a marking of the graph nodes
        self.graphTraversionMarker = False


    def graphTraversionMarkerReset(self):
        self.graphTraversionMarker = False

    def graphTraversionMarkerMarkVisited(self):
        self.graphTraversionMarker = True
    
    def graphTraversionMarkerMarkIsVisited(self):
        return self.graphTraversionMarker
    
    def configAddOutputSignal(self, name):
        # add an output signals to this block typically called by the block prototypes
        # NOTE: This just reservates that there will be an output
        #       the type is undefined at this point

        portNumber = len(self.OutputSignals)
        newSignal = Signal(self.sim, None, self, portNumber )
        newSignal.setName(name)

        self.OutputSignals.append( newSignal )

        return self


    def configDefineOutputTypes(self):
        # ask the block's prototype class instance to define the output types given
        # the input types (Please note that the input types are define by other blocks
        # whose outputs are connected to this block.)

        # build a list of input signals for this block
        inputSignalTypes = []

        for i in range(0, len(self.inputSignals)):
            inputSignalTypes.append( self.inputSignals[i].getDatatype() )

        # ask prototype to define output types
        outputSingalTypes = self.blockPrototype.configDefineOutputTypes( inputSignalTypes )

        # update all signals accordingly
        for i in range(0, len(self.OutputSignals)):

            signal = self.OutputSignals[i]
            signal.setDatatype(  outputSingalTypes[i]  )

        return


    def getName(self):
        return self.blockname

    def setName(self, name):
        self.blockname = name
        return self

    def toStr(self):
        return self.getName()

    def getBlockPrototype(self):
        return self.blockPrototype

    def getBlockId(self):
        return self.id # a unique id within the simulation the block is part of

    def getInputSignals(self):
        return self.inputSignals

    def getOutputSignals(self):
        return self.OutputSignals

    def GetOutputSignal(self, port):
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
    

    def encode_irpar(self):
        ipar, rpar = self.blockPrototype.encode_irpar()

        return ipar, rpar














