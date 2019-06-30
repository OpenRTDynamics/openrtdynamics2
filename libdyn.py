from contextlib import contextmanager
#import contextvars
from typing import Dict, List

from irpar import irparSet, irparElement, irparElement_container
from Signal import *
from Block import *

from DatatypePropagation import *


currentSimulation = 'none'

def detSimulationContext(sim):
    currentSimulation = sim

def showSimulationContext():
    print 

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

        # counter for simulation input signals
        # This determines the order of teh arguments of the generated c++ functions
        self.simulationInputSignalCounter = 0

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
        self.BlocksArray.append(blk)
        print("added block ", blk.getName() )

    # create and return a new simulation input signal
    def newInput(self, datatype):
        s = SimulationInputSignal(self, port=self.simulationInputSignalCounter, datatype=datatype )
        self.simulationInputSignalCounter += 1

        return s


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


    def GetInputInterface(self):
        # Build an input-interface for the ORTD interpreter
        # inform of a "inlist" structure

        print("External input signals:")
        
        for ExtInSig in self.ExternalConnectionsArray:
            ExtInSig.getDatatype().Show()

        return self.ExternalConnectionsArray


    def propagateDatatypesForward(self):

        self.datatypePropagation.fixateTypes()


    def CompileConnections(self):
        print("Compiling connections")

        # find out the output datatypes
        self.propagateDatatypesForward()

        










