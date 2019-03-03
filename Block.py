from typing import Dict, List

from Signal import *

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




class BlockPrototype:
    # This is a base class to be deviated from each block type.
    # It contains logic to handle the input/ output types and
    # the parameters.
    # In future, also the implementation might go into it



    def __init__(self):
        # collect and store parameters and connections to other blocks
        pass

    def setPropagatedInputTypes(self, InTypes : InputDefinitions ):
        # called when the inputs to this blocks already have been decicded on
        # the Block logic should check wheter these input types can be handles
        # and if so adapt the parameters / implementation. If no adaptino is
        # possible, return an error.
        pass

    def getOutputTypes(self):
        # shall return OutTypes : OutputDefinitions

        pass

    #def PropagatedOutputTypes(self, OutTypes):
    # Difficult to implement
    #    pass

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

    def getOperator(self):
        pass
    

    def generateCode(self):
        pass












  
class Block:
    # This decribes a block that is part of a Simulation
    # 
    # BlockPrototype - describes the block's prototype implementation
    #                  that defined IO, parameters, ...

    def __init__(self, sim, BlockPrototype : BlockPrototype, inputSignals : List[Signal], OutputDef : OutputDefinitions, blockname : str):
        self.sim = sim

        #operator, blocktype

        self.blockname = blockname

        print("Creating new block named ", blockname)

        # The blocks prototype function. e.g. to determine the port sizes and types
        # and to define the parameters
        self.BlockPrototype = BlockPrototype

        # The input singals in form of a list
        if inputSignals is None:
            self.inputSignals = []
        else:
            self.inputSignals = inputSignals # array of Signal

        # the definition of the output ports. Note: only the number of ports must be known. The types might be left open
        self.OutputDef = OutputDef 

        # create a new unique block id 
        self.id = sim.getNewBlockId()


        #self.InputDatatypes = []
        #self.OutputDatatypes = []

        # Create a list of output signals. The datatypes and sizes are undtermined untll getOutputTypes() of blocks prototype function is called
        #  ( : List[ Signal ] )
        outputPortNum = self.OutputDef.getNPorts()

        print("creating signals for ", outputPortNum, " output ports")

        self.OutputSignals = []
        for i in range(0, outputPortNum ):
            #print("* new signal")
            datatype = self.OutputDef.getType(i)
            if datatype is None:
                self.OutputSignals.append( Signal(sim, None, self, i ) )
            else:
                self.OutputSignals.append( Signal(sim, datatype, self, i ) )

        # get new block id
        self.id = sim.getNewBlockId()


    
    def checkIO(self):
        #
        # Check if the conntected inputs match
        #
        # TODO rework this to match  Inputs : InputDefinitions
        #

        pass


        # if not len(inlist) == self.Blocktype.getNInputs():
        #     #print("Number of inputs missmatch")
        #     raise ValueError('Number of inputs missmatch', len(inlist), self.Blocktype.getNOutputs())



        # for port in range(0, self.Blocktype.getNInputs() ):
        #     #print("* Checking input " + str(port) + ". It shall be " )
        #     #inlist[i].datatype.Show()
        #     #print("* It is ")


        #     BlocksType = self.Blocktype.getInputDataType(port)
        #     self.InputDatatypes.append( BlocksType )

        #     #BlocksType.Show()

        #     if not (inlist[port].datatype.isEqualTo(BlocksType) ):
        #         #print("Type missmatch for input #" + str(port) + ".")
        #         raise ValueError('Type missmatch for input # ', str(port) )


    def defineOutputSignals(self):
        
        #
        # REMARK: UNDER CONSTRUCTION
        #

        # get the output types for each port that are defined by the blocks prototype function
        # when the following call is executed
        self.OutputTypes = self.BlockPrototype.getOutputTypes() # type OutputDefinitions

        # create the output signals
        # ... TODO

        for port in range( self.OutputTypes.getNPorts() ):
            BlocksOutType = self.OutputTypes.getType(port)
            self.OutputSignals.append( Signal(sim, BlocksOutType, self, port) )  # connect source of signal to port 0 of block blk




        #OutputTypes.getNPorts()
        #OutputTypes.getType(self, i : int)

        #for i in OutputTypesList:
        #    pass
            

        # # Create the output signals
        # for port in range(0, self.Blocktype.getNOutputs() ):
        #     BlocksOutType = self.Blocktype.getOutputDataType(port)

        #     self.OutputDatatypes.append( BlocksOutType )

        #     # create the output signals
        #     self.OutputSignals.append( Signal(sim, BlocksOutType, self, port) )  # connect source of signal to port 0 of block blk


    def getName(self):
        return self.blockname

    def getBlockPrototype(self):
        return self.BlockPrototype

    def getBlockId(self):
        return self.id # a unique id within the simulation the block is part of

    def getOperator(self):
        return None
        #return self.Blocktype.getOperator()

    def getInSignals(self):
        return self.inputSignals

    def getOutputSignals(self):
        return self.OutputSignals

    def getOutputTypes(self):
        return self.OutputDef

    def getId(self):
        #return -1
        return self.id

    def GetOutputSignal(self, port):
        if port < 0:
            raise Exception('port < 0')

        if port >= len(self.OutputSignals): 
            raise Exception('port out of range')

        return self.OutputSignals[port]

    def encode_irpar(self):
        ipar, rpar = self.BlockPrototype.encode_irpar()

        return ipar, rpar


