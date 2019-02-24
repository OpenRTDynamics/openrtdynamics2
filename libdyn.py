from contextlib import contextmanager
#import contextvars
from typing import Dict, List

from irpar import irparSet, irparElement, irparElement_container





ORTD_DATATYPE_UNCONFIGURED = 0
ORTD_DATATYPE_FLOAT = (1 | (8 << 5))
ORTD_DATATYPE_SHORTFLOAT = 4
ORTD_DATATYPE_INT32 = 2
ORTD_DATATYPE_BOOLEAN = 3
ORTD_DATATYPE_EVENT = 5
ORTD_DATATYPE_BINARY = 6
ORTD_DATATYPE_UINT32 = 7
ORTD_DATATYPE_INT16 = 8
ORTD_DATATYPE_UINT16 = 9
ORTD_DATATYPE_INT8 = 10
ORTD_DATATYPE_UINT8 = 11


#BlockDictionary['const'] = { "btype" : 1, "intypes" : [], "insizes" : [], "outtypes" : [ORTD_DATATYPE_FLOAT], "outsizes" : [1]  }

# # TODO REMOVE THIS
# class Blocktype:
#     def __init__(self, description):
#         self.description = description

#         if not len(description['insizes']) == len(description['intypes']):
#             raise ValueError('missmatch of insizes and intypes', len(description['insizes']), len(description['intypes']) )

#         if not len(description['outsizes']) == len(description['outtypes']):
#             raise ValueError('missmatch of outsizes and outtypes', len(description['outsizes']), len(description['outtypes']))


#     def getOperator(self):
#         return self.description['operator']

#     def getBtype(self):
#         return self.description['btype']

#     def getInputDataType(self, port):
#         return DataType(self.description["intypes"][port], self.description["insizes"][port])

#     def getOutputDataType(self, port):
#         return DataType(self.description["outtypes"][port], self.description["outsizes"][port])

#     def getNOutputs(self):
#         return len(self.description["outtypes"])

#     def getNInputs(self):
#         return len(self.description["intypes"])


#     def encode_irpar(self, par):
#         # implement a generic irpar encoder
#         #ipar = [1, 2, 3]
#         #rpar = [0.1, 0.2, 0.3]

#         # TODO: here, multiple options (e.g., more modern ones) could be supported..
#         # par.ipar and par.rpar is only for backwards compatibility
#         ipar = par['ipar']
#         rpar = par['rpar']

#         return ipar, rpar


# # TODO REMOVE THIS
# class BlockDictionary:
#     def __init__(self):
#         self.Dict = {}

#     def addBlocktype(self, blocktype : Blocktype):
#         self.Dict[ blocktype.getOperator() ] = blocktype

#     def lookupOperator(self, operator : str):
#         return self.Dict[operator]


# BlockDict = BlockDictionary()

# BlockDict.addBlocktype(Blocktype(
#                         { "operator" : "const",
#                           "btype" : 60001 + 9,
#                           "intypes" : [],
#                           "insizes" : [],
#                           "outtypes" : [ORTD_DATATYPE_FLOAT],
#                           "outsizes" : [1]  })
#                        )

# BlockDict.addBlocktype(Blocktype(
#                         { "operator" : "constInt32",
#                           "btype" : 1,
#                           "intypes" : [],
#                           "insizes" : [],
#                           "outtypes" : [ORTD_DATATYPE_INT32],
#                           "outsizes" : [1]  })
#                        )


# BlockDict.addBlocktype(Blocktype(
#                         { "operator" : "sum",
#                           "btype" : 2,
#                           "intypes" : [ORTD_DATATYPE_FLOAT,ORTD_DATATYPE_FLOAT],
#                           "insizes" : [1,1],
#                           "outtypes" : [ORTD_DATATYPE_FLOAT],
#                           "outsizes" : [1]  })
#                        )

# BlockDict.addBlocktype(Blocktype(
#                         { "operator" : "compare",
#                           "btype" : 3,
#                           "intypes" : [ORTD_DATATYPE_FLOAT],
#                           "insizes" : [1],
#                           "outtypes" : [ORTD_DATATYPE_INT32],
#                           "outsizes" : [1]  })
#                        )



class DataType:
    def __init__(self, type : int, size : int):
        self.type = type
        self.size = size

    def isEqualTo(self, otherType):
        #print("DataType:isEqualTo " + str(self.size) + "==" + str(otherType.size) + " -- " + str(self.type) + " == " + str(otherType.type) )

        if self.size == otherType.size and self.type == otherType.type:
            return 1
        else:
            return 0

    def Show(self):
        print("Datatype: type=" + str(self.type) + " size=" + str(self.size) )


class Signal:
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):
        self.sim = sim
        self.datatype = datatype
        self.sourceBlock = sourceBlock
        self.sourcePort = sourcePort  # counting starts at zero

        #if sourceBlock == None:
            # create a signal without any specified origin

    def setequal(self, From ):
        #if self.sim != From.sim:
        #    throw("setequal: From signal must be from the same simulation")

        if self.datatype == None:
            self.datatype = From.datatype
        elif not self.datatype.isEqualTo( From.datatype ):
            throw("setqual: datatype missmatch")
        else:
            self.datatype = From.datatype

        self.sourceBlock = From.sourceBlock
        self.sourcePort = From.sourcePort

    def getDatatype(self):
        return self.datatype

    def ShowOrigin(self):
        print("port " + str(self.sourcePort) + " of block #" + str(self.sourceBlock.getId()) )






















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
        return self.ports(port)


class OutputDefinitions:
    # This defines a list of datatypes for each output port
    # if the output type of one port is undecided
    # the list element is None
    def __init__( self, ports : List[ DataType ]  ):

        self.ports = ports

    def getNPorts(self):
        return len( self.ports )

    def getType(self, port : int):
        return self.ports(port)




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

    def __init__(self, sim, BlockPrototype : BlockPrototype, Inputs : InputDefinitions, OutputDef : OutputDefinitions):
        self.sim = sim

        #operator, blocktype

        # The blocks prototype function. e.g. to determine the port sizes and types
        # and to define the parameters
        self.BlockPrototype = BlockPrototype

        # The input singals in form of a list
        self.Inputs = Inputs # array of Signal

        # the definition of the output ports. Note: only the number of ports must be known. The types might be left open
        self.OutputDef = OutputDef 

        # create a new unique block id 
        self.id = sim.getNewBlockId()


        #self.InputDatatypes = []
        #self.OutputDatatypes = []

        # Create a list of output signals. The datatypes and sizes are undtermined untll getOutputTypes() of blocks prototype function is called
        #  ( : List[ Signal ] )
        self.OutputSignals = []
        for i in range(0, self.OutputDef.getNPorts() ):
            self.OutputSignals.append( Signal(sim ) )

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




    def getBlockPrototype(self):
        return self.BlockPrototype

    def getBlockId(self):
        return self.id # a unique id within the simulation the block is part of

    def getOperator(self):
        return None
        #return self.Blocktype.getOperator()

    def getInSignals(self):
        return self.inlist

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






# # TODO Derive from BlockPrototype
# class SubSimBlock(Block):

#     def __init__(self, sim ,  Blocktype : Blocktype, inlist : List[Signal], par):
#         Block.__init__(self, sim, Blocktype, inlist, par )
#         self.SubSimArray = []

#     def addSubSimulation(self, sim):
#         self.SubSimArray.append(sim)

      




class Simulation:
    def __init__(self, UpperLevelSim , name : str ):
        if UpperLevelSim is None:
            print("New simulation")
        else:
            print("New simulation as a child of " + UpperLevelSim.getName())

        self.UpperLevelSim = UpperLevelSim
        self.name = name
        self.BlocksArray = []
        self.BlockIdCounter = 200 # start at 200 to reserve some space below
        self.SimulationFinished = False

        self.ReturnList = []

    def getName(self):
        return self.name

    def getNewBlockId(self):
        self.BlockIdCounter += 1
        return self.BlockIdCounter

    def addBlock(self, Blk : Block):
        if self.SimulationFinished:
            throw("Cannot add blocks to a finished simulation/subsystem")

        self.BlocksArray.append(Blk)
        #print("added a block with blocktype " + str(Blk.getBlocktype() ) )




    def Return(self, sigList : List[Signal]):
        for sig in sigList:
            self.ReturnList.append(sig)



    def ShowBlocks(self):
        print("-----------------------------")
        print("Blocks in simulation " + self.name + ":")
        print("-----------------------------")

        for blk in self.BlocksArray:
            print("operator: " + blk.getOperator() + " Blocktype: " + str( blk.getBlocktype() ) )
            print("Inputs:")
            for inSig in blk.getInSignals():
                inSig.ShowOrigin()


    def FinishSimulation(self):
        if self.SimulationFinished:
            return
            #throw("Cannot finish an already finished simulation/subsystem")


        # Finisih the simulation
        self.CompileConnections()

        # mark simulation as finished
        self.SimulationFinished = True


    def GetInputInterface(self):
        # Build an input-interface for the ORTD interpreter
        # inform of a "inlist" structure


        if self.SimulationFinished == False:
            throw("Simulation not finished to far.")


        #inlist = []
        print("External input signals:")
        

        for ExtInSig in self.ExternalConnectionsArray:

            ExtInSig.getDatatype().Show()

#            print(".) " + str(  ) )
            #inlist.append( ExtInSig )


        return self.ExternalConnectionsArray



    def TraverseBlockInExecOrder(self):
        # TODO:
        #
        # Go through all block along their connection lines
        # 1) start with all source blocks (only outputs)
        #


        pass



    def CompileConnections(self):

        print("Compiling connections")


        # TODO: Call defineOutputSignals of each block
        # using TraverseBlockInExecOrder



        # Array to store the connections that remain inside the simulation 
        self.InternalConnectionsArray = []

        # Array to store the connections that do not have sources within this simulation 
        self.ExternalConnectionsArray = []


        # Number of connections
        Nconnections = 0

        for blk in self.BlocksArray:
            # collect the connections

            #for inSig in blk.getInSignals():
            blk_inlist = blk.getInSignals()
            for i in range(0, len(blk_inlist)):

                inSig = blk_inlist[i]

                if inSig.sim == self:
                    # This is simulation internal connection
                    src_id = inSig.sourceBlock.getBlockId()
                    src_port = inSig.sourcePort

                    dst_id = blk.getBlockId()
                    dst_port = i


                    self.InternalConnectionsArray.append( (src_id, src_port, dst_id, dst_port) )

                    # store this connection
                    Nconnections += 1

                else:
                    # This signal comes from an upper level simulation

                    self.ExternalConnectionsArray.append(inSig)








    def encode_irpar(self):
        print("Encoding simulation into irpar-format")

        # create new irpar set
        irpar = irparSet()

        IRPAR_LIBDYN_BLOCK = 100
        IRPAR_LIBDYN_CONNLIST = 101


        for blk in self.BlocksArray:

            # get block's encoded parameters
            ipar, rpar = blk.encode_irpar()

            btype = blk.getBlocktype().getBtype()
            eventlist_len = 1
            event = 0

            header = [ btype, blk.getBlockId(), len(ipar), len(rpar), eventlist_len, event ]

            irpar.AddElemet(irparElement(blk.getBlockId(), IRPAR_LIBDYN_BLOCK, header + ipar, rpar ))



        # encode block connections
        cltype = 0
        entries = -1 # unknown so far
        listelesize = 8
        listofs = 4 # header length

        header = [ cltype, entries, listelesize, listofs ]

        # collector variable
        dsave = []
        dsave += header

        # Number of connections
        Nconnections = 0

        for conn in self.InternalConnectionsArray:
            # collect the connections
            (src_id, src_port, dst_id, dst_port) = conn
            connection_encoded = [ 0, src_id, src_id, src_port,   0, dst_id, dst_id, dst_port ]

            # store this connection
            dsave += connection_encoded
            Nconnections += 1

        # modidy header..
        dsave[1] = Nconnections

        id = 100
        irpar.AddElemet(irparElement(id, IRPAR_LIBDYN_CONNLIST, dsave, [] ))

        return irpar









    def encode_irpar_old(self):

        # create new irpar set
        irpar = irparSet()

        IRPAR_LIBDYN_BLOCK = 100
        IRPAR_LIBDYN_CONNLIST = 101


        for blk in self.BlocksArray:

            # get block's encoded parameters
            ipar, rpar = blk.encode_irpar()

            btype = blk.getBlocktype().getBtype()
            eventlist_len = 1
            event = 0

            header = [ btype, blk.getBlockId(), len(ipar), len(rpar), eventlist_len, event ]

            #EncodedBlockList.append(header)


            #new_irparam_elemet(sim.parlist, id, IRPAR_LIBDYN_BLOCK, [header; ipar(:)], [rpar(:)]);
            irpar.AddElemet(irparElement(blk.getBlockId(), IRPAR_LIBDYN_BLOCK, header + ipar, rpar ))



        # encode block connections
        # (Build connectionlist)

        #EncodedConnectionList = []

        cltype = 0
        entries = -1 # unknown so far
        listelesize = 8
        listofs = 4 # header length

        header = [ cltype, entries, listelesize, listofs ]



        # collector variable
        dsave = []
        dsave += header

        # Number of connections
        Nconnections = 0

        for blk in self.BlocksArray:


            # collect the connections

            #for inSig in blk.getInSignals():
            blk_inlist = blk.getInSignals()
            for i in range(0, len(blk_inlist)):

                inSig = blk_inlist[i]

                src_id = inSig.sourceBlock.getBlockId()
                src_port = inSig.sourcePort
                dst_id = blk.getBlockId()
                dst_port = i

                connection_encoded = [ 0, src_id, src_id, src_port,   0, dst_id, dst_id, dst_port ]

                # store this connection
                dsave += connection_encoded
                Nconnections += 1

                #EncodedConnectionList.append(connection_encoded)


        # connection_encoded shall contain the concatensation of all

        # modidy header..
        dsave[1] = Nconnections

        id = 100
        irpar.AddElemet(irparElement(id, IRPAR_LIBDYN_CONNLIST, dsave, [] ))



        #ipar, rpar = irpar.combine_irparam()
        #return ipar, rpar

        return irpar

    def irparWrap(self, id : int):

        self.FinishSimulation()


        irpar = irparSet()

        irparNest = self.encode_irpar()
        iparNest, rparNest = irparNest.combine_irparam()

        irpar.AddElemet(irparElement_container(id, iparNest, rparNest))

        return irpar

    def export_ortdrun(self, ProgramName: str):

        # wrap the simulation into a container with id 901 which will be opened by ortdrun
        id = 901
        irpar = self.irparWrap(id)

        ipar, rpar = irpar.combine_irparam()


        with open(ProgramName + '.ipar', 'w') as f:
            for d in ipar:
                f.write('%d\n' % d)


        with open(ProgramName + '.rpar', 'w') as f:
            for d in rpar:
                f.write('%f\n' % d)














