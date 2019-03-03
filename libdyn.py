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


class Blocktype:
    def __init__(self, description):
        self.description = description

        if not len(description['insizes']) == len(description['intypes']):
            raise ValueError('missmatch of insizes and intypes', len(description['insizes']), len(description['intypes']) )

        if not len(description['outsizes']) == len(description['outtypes']):
            raise ValueError('missmatch of outsizes and outtypes', len(description['outsizes']), len(description['outtypes']))


    def getOperator(self):
        return self.description['operator']

    def getBtype(self):
        return self.description['btype']

    def getInputDataType(self, port):
        return DataType(self.description["intypes"][port], self.description["insizes"][port])

    def getOutputDataType(self, port):
        return DataType(self.description["outtypes"][port], self.description["outsizes"][port])

    def getNOutputs(self):
        return len(self.description["outtypes"])

    def getNInputs(self):
        return len(self.description["intypes"])


    def encode_irpar(self, par):
        # implement a generic irpar encoder
        #ipar = [1, 2, 3]
        #rpar = [0.1, 0.2, 0.3]

        # TODO: here, multiple options (e.g., more modern ones) could be supported..
        # par.ipar and par.rpar is only for backwards compatibility
        ipar = par['ipar']
        rpar = par['rpar']

        return ipar, rpar


class BlockDictionary:
    def __init__(self):
        self.Dict = {}

    def addBlocktype(self, blocktype : Blocktype):
        self.Dict[ blocktype.getOperator() ] = blocktype

    def lookupOperator(self, operator : str):
        return self.Dict[operator]


BlockDict = BlockDictionary()

BlockDict.addBlocktype(Blocktype(
                        { "operator" : "const",
                          "btype" : 60001 + 9,
                          "intypes" : [],
                          "insizes" : [],
                          "outtypes" : [ORTD_DATATYPE_FLOAT],
                          "outsizes" : [1]  })
                       )

BlockDict.addBlocktype(Blocktype(
                        { "operator" : "constInt32",
                          "btype" : 1,
                          "intypes" : [],
                          "insizes" : [],
                          "outtypes" : [ORTD_DATATYPE_INT32],
                          "outsizes" : [1]  })
                       )


BlockDict.addBlocktype(Blocktype(
                        { "operator" : "sum",
                          "btype" : 2,
                          "intypes" : [ORTD_DATATYPE_FLOAT,ORTD_DATATYPE_FLOAT],
                          "insizes" : [1,1],
                          "outtypes" : [ORTD_DATATYPE_FLOAT],
                          "outsizes" : [1]  })
                       )

BlockDict.addBlocktype(Blocktype(
                        { "operator" : "compare",
                          "btype" : 3,
                          "intypes" : [ORTD_DATATYPE_FLOAT],
                          "insizes" : [1],
                          "outtypes" : [ORTD_DATATYPE_INT32],
                          "outsizes" : [1]  })
                       )


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
    def __init__(self, sim, datatype, sourceBlock = None, sourcePort = None):
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




  
class Block:

    def __init__(self, sim  , Blocktype : Blocktype, inlist : List[Signal], par):
        self.sim = sim

        #operator, blocktype

        #self.operator =
        self.Blocktype = Blocktype
        self.id = sim.getNewBlockId()

        self.inlist = inlist # array of Signal
        self.par = par

        self.InputDatatypes = []
        self.OutputDatatypes = []

        self.OutputSignals = []



        # check insizes

        #self.inDatatypes =

        if not len(inlist)  == self.Blocktype.getNInputs():
            #print("Number of inputs missmatch")
            raise ValueError('Number of inputs missmatch', len(inlist), self.Blocktype.getNOutputs())



        for port in range(0, self.Blocktype.getNInputs() ):
            #print("* Checking input " + str(port) + ". It shall be " )
            #inlist[i].datatype.Show()
            #print("* It is ")


            BlocksType = self.Blocktype.getInputDataType(port)
            self.InputDatatypes.append( BlocksType )

            #BlocksType.Show()

            if not (inlist[port].datatype.isEqualTo(BlocksType) ):
                #print("Type missmatch for input #" + str(port) + ".")
                raise ValueError('Type missmatch for input # ', str(port) )

        for port in range(0, self.Blocktype.getNOutputs() ):
            BlocksOutType = self.Blocktype.getOutputDataType(port)

            self.OutputDatatypes.append( BlocksOutType )

            # create the output signals
            self.OutputSignals.append( Signal(sim, BlocksOutType, self, port) )  # connect source of signal to port 0 of block blk

        self.id = sim.getNewBlockId()


    def getBlocktype(self):
        return self.Blocktype

    def getBlockId(self):
        return self.id # a unique id within the simulation the block is part of

    def getOperator(self):
        return self.Blocktype.getOperator()

    def getInSignals(self):
        return self.inlist

    def getId(self):
        #return -1
        return self.id

    def GetOutputSignal(self, port):
        return self.OutputSignals[port]

    def encode_irpar(self):
        ipar, rpar = self.Blocktype.encode_irpar(self.par)

        return ipar, rpar


class SubSimBlock(Block):

    def __init__(self, sim ,  Blocktype : Blocktype, inlist : List[Signal], par):
        Block.__init__(self, sim, Blocktype, inlist, par )
        self.SubSimArray = []

    def addSubSimulation(self, sim):
        self.SubSimArray.append(sim)

      

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



    def CompileConnections(self):

        print("Compiling connections")


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









def ld_block(sim, operator : str, inlist, par):
    # lookup operator...
    Blocktype = BlockDict.lookupOperator(operator)

    #
    blk = Block(sim, Blocktype, inlist, par)
    sim.addBlock(blk)

    #print("ld_block: new block with id " + str( blk.getId() ) )

    # create the output signals
    y1 = blk.GetOutputSignal(0)

    return y1





############################



# [sim,sum_] = ld_add(sim, events, inp_list, fak_list)
def ld_add(sim : Simulation, inp_list : List[Signal], fak_list : List[float]):

    BT = Blocktype(
        {"operator": "const",
         "btype": 12,
         "intypes": [ORTD_DATATYPE_FLOAT,ORTD_DATATYPE_FLOAT],
         "insizes": [1,1],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    if len(inp_list) != 2:
        throw("inp_list must have exactly 2 elements")

    par = { 'ipar' : [], 'rpar' : fak_list }
    inlist = inp_list

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)

    # create the output signals
    sum = blk.GetOutputSignal(0)

    return sum


# [sim, out] = ld_delay(sim, events, u, N)
def ld_delay(sim : Simulation, u : Signal, N : int):

    BT = Blocktype(
        {"operator": "const",
         "btype": 60001 + 24,
         "intypes": [ORTD_DATATYPE_FLOAT],
         "insizes": [1],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    if N <= 0:
        throw("N <= 0 !")

    par = { 'ipar' : [N], 'rpar' : [] }
    inlist = [u]

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)


    # create the output signals
    y = blk.GetOutputSignal(0)

    return y


def ld_const(sim : Simulation, val : float):

    BT = Blocktype(
        {"operator": "const",
         "btype": 40,
         "intypes": [],
         "insizes": [],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    par = { 'ipar' : [], 'rpar' : [val] }
    inlist = []

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)

    #print("ld_const: new block with id " + str( blk.getId() ) )

    # create the output signals
    y1 = blk.GetOutputSignal(0)

    return y1




def ld_printf(sim : Simulation, u : Signal, name : str):

    vlen = u.datatype.size

    if u.datatype.type != ORTD_DATATYPE_FLOAT:
        throw("u.datatype.type != ORTD_DATATYPE_FLOAT !")


    BT = Blocktype(
        {"operator": "const",
         "btype": 170,
         "intypes": [ORTD_DATATYPE_FLOAT],
         "insizes": [vlen],
         "outtypes": [],
         "outsizes": []})

    # tostr
    strAscii = []
    for code in map(ord, name):
        #print(code)
        strAscii += [code]



    #
    par = { 'ipar' : [vlen, len(strAscii)] + strAscii, 'rpar' : [] }
    inlist = [u]

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)

    #print("ld_printf: new block with id " + str( blk.getId() ) )

    return



#[sim,y] = ld_play_simple(sim, events, r)
def ld_play_simple(sim :Simulation , r : List[float]):

    BT = Blocktype(
        {"operator": "const",
         "btype": 100,
         "intypes": [],
         "insizes": [],
         "outtypes": [ORTD_DATATYPE_FLOAT],
         "outsizes": [1]})

    #
    if len(r) <= 0:
        throw("length(r) <= 0 !")

    initial_play = 1
    hold_last_value = 0
    mute_afterstop = 0

    par = { 'ipar' : [len(r), initial_play, hold_last_value, mute_afterstop], 'rpar' : r }
    inlist = []

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)


    # create the output signals
    y = blk.GetOutputSignal(0)

    return y



# [sim] = ld_savefile(sim, events, fname, source, vlen), libdyn_new_blk_filedump
def ld_savefile(sim : Simulation, fname : str, source : Signal):

    vlen = source.datatype.size

    if source.datatype.type != ORTD_DATATYPE_FLOAT:
        throw("source.datatype.type != ORTD_DATATYPE_FLOAT !")

    BT = Blocktype(
        {"operator": "const",
         "btype": 130,
         "intypes": [ORTD_DATATYPE_FLOAT],
         "insizes": [vlen],
         "outtypes": [],
         "outsizes": []})

    if vlen <= 0:
        throw("vlen <= 0 !")

    # tostr
    strAscii = []
    for code in map(ord, fname):
        #print(code)
        strAscii += [code]

    autostart = 1
    maxlen = 0

    #
    par = { 'ipar' : [maxlen, autostart, vlen, len(strAscii)] + strAscii, 'rpar' : [] }
    inlist = [source]

    #
    blk = Block(sim, BT, inlist, par)
    sim.addBlock(blk)


    return






@contextmanager
def ld_subsim(sim):
    print("create triggered subsimulation" )

    nestedsim = Simulation(sim, 'IFsub')

    yield nestedsim

    nestedsim.FinishSimulation()

    inlist = nestedsim.GetInputInterface()

    print("--- The following inputs go to the nested simulation ---")

    for i in inlist:

        print(  i  )

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



    print("finish triggered subsimulation")



# @contextmanager
# def ld_IF(sim, ConditionSignal):
#     print("create triggered subsimulation" )

#     nestedsim = Simulation(sim, 'IFsub')

#     yield nestedsim

#     print("finish triggered subsimulation")



# new simulation
sim = Simulation(None, 'main')

# blocks
c1 = ld_const(sim, 1.123)
#c2 = ld_const(sim, 1.23124)

c2 = ld_play_simple(sim, r=[1,2,3,4,5,6,7,8,9])

# a feedback
feedback = Signal(sim, DataType( ORTD_DATATYPE_FLOAT, 1 ))

ld_printf(sim, feedback, "feedback value is")

#
sum = ld_add(sim, inp_list=[c1, c2], fak_list=[1,-1])


sum_delayed = ld_delay(sim, u=sum, N=10)

feedback.setequal( sum_delayed )

ld_printf(sim, sum, "value is")
ld_printf(sim, sum_delayed, "delayed value is")

ld_printf(sim, c2, "another print..")
ld_printf(sim, c2, "and a 3rd one")

ld_savefile(sim, fname="SimulationOutput.dat", source=c2)


print(sim)

with ld_subsim(sim) as sim2:
    ld_printf(sim2, sum, "This is a printf in a sub-simulation")

    ret = ld_delay(sim2, u=sum, N=1)

    sim2.Return( [ret] )





print(sim)

# with ld_IF(sim, condition) as sim:
#     #pass
#     print("define simulation triggered by if")







# finish
sim.export_ortdrun('RTMain')
#sim.ShowBlocks()










if False:
    sim = Simulation(None, 'main')

    c1 = ld_block(sim, 'const', [], 2)
    c2 = ld_block(sim, 'const', [], 3)

    i_int32 = ld_block(sim, 'constInt32', [], 30)

    #print("####")
    #sum2 = ld_block(sim, 'sum', [i_int32, i_int32], [0.3, 2])
    #print("####")


    sum = ld_block(sim, 'sum', [c1, c2], [0.3, 2])

    condition = ld_block(sim, 'compare', [sum], 0)

    # sim.ShowBlocks()

    #blk = Block(sim, 100, [], [])
    #condition = Signal(sim, DataType(1,1), blk, 1 )


    #ipar, rpar = sim.encode_irpar()

    #print(ipar)
    #print(rpar)

    sim.export_ortdrun('RTMain')



#    with ld_IF(sim, condition) as sim:
#        print("define simulation triggered by if")














