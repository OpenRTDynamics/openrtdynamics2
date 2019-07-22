from contextlib import contextmanager
#import contextvars
from typing import Dict, List

from irpar import irparSet, irparElement, irparElement_container
from Signal import *
from Block import *

from DatatypePropagation import *


# currentSimulation = 'none'

# def detSimulationContext(sim):
#     currentSimulation = sim

# def showSimulationContext():
#     print 

class Simulation:
    def __init__(self, upperLevelSim , name : str ):
        if upperLevelSim is None:
            print("New simulation")
        else:
            print("New simulation as a child of " + upperLevelSim.getName())

        self.UpperLevelSim = upperLevelSim
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
    # def newInput(self, datatype):
    #     s = SimulationInputSignal(self, port=self.simulationInputSignalCounter, datatype=datatype )
    #     self.simulationInputSignalCounter += 1

    #     return s


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

        def createBlockNode(nodes_array_index, block):
            idstr = 'bid_' + str( block.getBlockId() )

            node = {}
            node['name'] = block.getName()
            node['type'] = 'block'

            node['tostr'] = block.toStr()
            node['id'] = idstr
            node['nodes_array_index'] = nodes_array_index

            return node, idstr


        def createSimulationInputNode(nodes_array_index, inSig):
            # append a node that stands for a simulation input
            idstr = 'insig_' + inSig.getName()

            node = {}
            node['name'] = 'in_' + inSig.getName()
            node['type'] = 'simulation_input'

            # node['tostr'] = block.toStr()
            node['id'] = idstr
            node['nodes_array_index'] = nodes_array_index

            return node, idstr

        def createLink(signal, sourceBlock, destBlock):
            # create a link in-between blocks

            link = {}
            link['tostr'] = signal.toStr()
            link['name'] = signal.getName()

            link['source'] = ''
            link['target'] = ''

            link['source_bid'] = sourceBlock.getBlockId()
            link['target_bid'] = destBlock.getBlockId()

            link['source_key'] = 'bid_' + str( sourceBlock.getBlockId() )
            link['target_key'] = 'bid_' + str( destBlock.getBlockId() )

            return link

        def createLinkFromSimulationInput(signal, destBlock):
            # create a link between a maker-node for the simulation input signal
            # anf the destination block 

            link = {}
            link['tostr'] = signal.toStr()
            link['name'] = signal.getName()

            link['source'] = ''
            link['target'] = ''

            link['target_bid'] = destBlock.getBlockId()

            link['source_key'] = idstr
            link['target_key'] = 'bid_' + str( destBlock.getBlockId() )

            return link



        # init/reset the list of all nodes and links
        nodes_array = []
        nodes_hash = {}
        links = []

        # create a node for each block in the simulation
        nodes_array_index = 0
        for block in self.BlocksArray:

            node, idstr = createBlockNode(nodes_array_index, block)

            nodes_array.append( node )
            nodes_hash[idstr] = node

            nodes_array_index += 1

        
        # build links
        for blk in self.BlocksArray:

            # list input singals
            if len( blk.getInputSignals() ) > 0:
                print(Fore.RED + "  input signals")
                for inSig in blk.getInputSignals():
                    print(Style.DIM + "    - " + inSig.toStr() )


                    if isinstance(inSig.lookupSource(), BlockOutputSignal):
                        # this is a block to block connection. Create a normal link in-between 

                        sourceBlock = inSig.getSourceBlock()

                        link = createLink(signal=inSig, sourceBlock=sourceBlock, destBlock=blk)
                        links.append( link )

                    if isinstance(inSig, SimulationInputSignal):
                        # this is an input to the simulation: add a special marker node
                        # and add a link from this newly created node to the block

                        # TODO: only create this node, of it does not already exist
                        node, idstr = createSimulationInputNode(nodes_array_index, inSig)

                        nodes_array.append( node )
                        nodes_hash[idstr] = node
                        nodes_array_index += 1

                        link = createLinkFromSimulationInput(inSig, blk)

                        links.append( link )



        # create nodes/links/something for the simulation outputs
        # (TODO)


        # finish the graph structure
        graph = {}

        graph['nodes_hash'] = nodes_hash
        graph['nodes'] = nodes_array # d3 requires an array
        graph['links'] = links

        # print graph
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

        for block in self.BlocksArray:
            block.verifyInputSignals()

        # find out the output datatypes
        self.propagateDatatypesForward()

        










