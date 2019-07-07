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
        self.BlockIdCounter = 0
        self.signalIdCounter = 0

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

    def exportGraph(self):

        # remove from this class and move to aonther class 'visualization' or 'editor'

# {
#     "nodes":[
#           {"name":"node1","group":1},
#           {"name":"node2","group":1},
#           {"name":"node3","group":1},
#           {"name":"node4","group":1}
#       ],
#       "links":[
#           {"source":1,"target":0,"weight":10}
#       ]
#   }



        # build list of all nodes/blocks
        nodes = []
        links = []

        for block in self.BlocksArray:

            node = {}
            node['name'] = block.getName()
            node['tostr'] = block.toStr()
            node['id'] = 'bid_' + str( block.getBlockId() )

            nodes.append( node )

        


        # build links


        for blk in self.BlocksArray:

            # list input singals
            if len( blk.getInputSignals() ) > 0:
                print(Fore.RED + "  input signals")
                for inSig in blk.getInputSignals():
                    print(Style.DIM + "    - " + inSig.toStr() )


                    sourceBlock = inSig.getSourceBlock()
                    if sourceBlock is not None:

                        link = {}
                        link['tostr'] = inSig.toStr()
                        link['name'] = inSig.getName()

                        link['sourceId'] = 'bid_' + str( sourceBlock.getBlockId() )
                        link['targetId'] = 'bid_' + str( blk.getBlockId() )

                        link['source'] = sourceBlock.getBlockId() - 1
                        link['target'] = blk.getBlockId() - 1

                        link['source'] = 'bid_' + str( sourceBlock.getBlockId() )
                        link['target'] = 'bid_' + str( blk.getBlockId() )

                        links.append( link )

                    else:
                        # this is typically an input to the simulation

                        pass




            # # list output singals
            # if len( blk.getOutputSignals() ) > 0:
            #     print(Fore.GREEN + "  output signals")
            #     for inSig in blk.getOutputSignals():
            #         print(Style.DIM + "    - " + inSig.toStr() )
        graph = {}

        graph['nodes'] = nodes
        graph['links'] = links

        # print(graph)
        import json
        print(json.dumps(graph, indent=4, sort_keys=True))

        #
        return graph





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

        










