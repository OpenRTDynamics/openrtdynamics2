from contextlib import contextmanager
#import contextvars
from typing import Dict, List

from irpar import irparSet, irparElement, irparElement_container
from Signal import *
from Block import *

from DatatypePropagation import *



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
        self.signalIdCounter = 1000
        self.SimulationFinished = False

        self.ReturnList = []

        # manager to determine datatypes as new blocks are added
        self.datatypePropagation = DatatypePropagation(self)

    def getName(self):
        return self.name

    def getNewBlockId(self):
        self.BlockIdCounter += 1
        return self.BlockIdCounter

    # get a new unique id for creating a signal
    def getNewSignalId(self):
        self.signalIdCounter += 1
        return self.signalIdCounter


    def addBlock(self, blk : Block):
        if self.SimulationFinished:
            raise("Cannot add blocks to a finished simulation/subsystem")

        self.BlocksArray.append(blk)
        print("added block ", blk.getName() )




    def Return(self, sigList : List[Signal]):
        for sig in sigList:
            self.ReturnList.append(sig)



    def ShowBlocks(self):
        print("-----------------------------")
        print("Blocks in simulation " + self.name + ":")
        print("-----------------------------")

        for blk in self.BlocksArray:
            print(Fore.YELLOW + "* " + Style.RESET_ALL + "'" + blk.getName() + "' (" + str(blk.getBlockId()) + ")"  )

            # list input singals
            if len( blk.getInputSignals() ) > 0:
                print(Fore.RED + "  input signals")
                for inSig in blk.getInputSignals():
                    print(Style.DIM + "    - " + inSig.toStr() )

            # list output singals
            if len( blk.getOutputSignals() ) > 0:
                print(Fore.GREEN + "  output signals")
                for inSig in blk.getOutputSignals():
                    print(Style.DIM + "    - " + inSig.toStr() )


    def getBlocksArray(self):
        return self.BlocksArray


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
            raise("Simulation not finished to far.")


        #inlist = []
        print("External input signals:")
        

        for ExtInSig in self.ExternalConnectionsArray:

            ExtInSig.getDatatype().Show()

#            print(".) " + str(  ) )
            #inlist.append( ExtInSig )


        return self.ExternalConnectionsArray



    def traverse(self, initialBlocks : List[Block] ):

        pass


    def propagateDatatypesForward(self):

        self.datatypePropagation.fixateTypes()


    def buildExecutionlist(self):
        # TODO: remove if uneeded


        # TODO:
        #
        # Go through all block and their respective output signals and check 
        # which signal value can be computed first.


        # find all signals that are defined with fixed datatypes
        for blk in self.BlocksArray:
            #print("operator: " + blk.getOperator() + " Blocktype: " + str( blk.getBlocktype() ) )
            

            print("-- block " , blk.getName(),  " outputs --")
            outputSignals = blk.getOutputSignals()

            if outputSignals is None:
                continue

            # iterate over all output signal and check if their value is computable
            for outputSignal in outputSignals:
                
                
                pass


    def CompileConnections(self):

        print("Compiling connections")


        # find out the output datatypes
        self.propagateDatatypesForward()

        


        return
        


        # TODO: remove if uneeded


        # Array to store the connections that remain inside the simulation 
        self.InternalConnectionsArray = []

        # Array to store the connections that do not have sources within this simulation 
        self.ExternalConnectionsArray = []


        # Number of connections
        Nconnections = 0

        for blk in self.BlocksArray:
            # collect the connections

            #for inSig in blk.getInSignals():
            blk_inlist = blk.getInputSignals()
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
            blk_inlist = blk.getInputSignals()
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














