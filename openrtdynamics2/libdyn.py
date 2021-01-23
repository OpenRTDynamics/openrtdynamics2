from contextlib import contextmanager
from typing import Dict, List

from .irpar import irparSet, irparElement, irparElement_container
from .signals import *
from .Block import *

from .datatype_propagation import *



# TODO: rename this to System
class Simulation:
    def __init__(self, upperLevelSim, name : str ):
        
        if upperLevelSim is None:
            # This system is a main system (no upper-level systems)
            # print("New system (top-level system)")
            pass
        else:
            # print("New system as a subsystem of " + upperLevelSim.getName())
            pass

        self.UpperLevelSim = upperLevelSim
        self._name = name
        self.BlocksArray = []

        # counter for system input signals
        # This determines the order of teh arguments of the generated c++ functions
        self.simulationInputSignalCounter = 0

        self._top_level_system = None

        if upperLevelSim is None:
            self._top_level_system = self

            self.BlockIdCounter = 0
            self.signalIdCounter = 0

            # manager to determine datatypes as new blocks are added
            # only for the highest-level system -- subsystems use the 
            # dataatyüe propagation of the main system
            self.datatypePropagation = DatatypePropagation(self)

        else:
            self._top_level_system = upperLevelSim._top_level_system

            # # share the counter of the 
            # self.BlockIdCounter = upperLevelSim.BlockIdCounter
            # self.signalIdCounter = upperLevelSim.signalIdCounter

            # re-use the upper-level propagation
            self.datatypePropagation = upperLevelSim.datatypePropagation

        # components
        self.components_ = {}

        # subsystems
        self._subsystems = []

        # primary outputs
        self._output_signals = []

        # signals that must be computed 
        self._signals_mandatory_to_compute = []

        # the results of the compilation of this system
        self.compilationResult = None

    def getName(self):
        return self._name

    @property
    def name(self):
        return self._name

    @property
    def parent_system(self):
        return self.UpperLevelSim 

    def getNewBlockId(self):
        self._top_level_system.BlockIdCounter += 1
        return self._top_level_system.BlockIdCounter

    # get a new unique id for creating a signal
    def getNewSignalId(self):
        self._top_level_system.signalIdCounter += 1
        return self._top_level_system.signalIdCounter

    def appendNestedSystem(self, system):
        self._subsystems.append( system )

    @property
    def subsystems(self):
        return self._subsystems

    def addBlock(self, blk : Block):
        self.BlocksArray.append(blk)

    # TODO: remove this?
    def set_primary_outputs(self, outputSignals):
        self._output_signals = outputSignals

    def append_primay_ouput(self, outputSignals):
        self._output_signals.append(outputSignals)
    
    @property
    def primary_outputs(self):
        return self._output_signals


    def add_signal_mandatory_to_compute(self, signal):
        self._signals_mandatory_to_compute = self._signals_mandatory_to_compute + [ signal ]

    @property
    def signals_mandatory_to_compute(self):
        return self._signals_mandatory_to_compute


    def ShowBlocks(self):
        print("-----------------------------")
        print("Blocks in simulation " + self._name + ":")
        print("-----------------------------")

        for blk in self.BlocksArray:
            print(Fore.YELLOW + "* " + Style.RESET_ALL + "'" + blk.name + "' (" + str(blk.id) + ")"  )

            # list input singals
            print(Fore.RED + "  input signals")
            if blk.getInputSignals() is not None and len( blk.getInputSignals() ) > 0:
                for inSig in blk.getInputSignals():
                    print(Style.DIM + "    - " + inSig.toStr() )

            else:
                print(Style.DIM + "    * undef *")

            # list output singals
            if len( blk.getOutputSignals() ) > 0:
                print(Fore.GREEN + "  output signals")
                for inSig in blk.getOutputSignals():
                    print(Style.DIM + "    - " + inSig.toStr() )

        print()
        print("  nested subsystems")
        for sys in self._subsystems:
            print("  - " + sys.getName() )

    @property
    def components(self):
        return self.components_


    def exportGraph(self):
        # TODO: remove from this class and move to aonther class 'visualization' or 'editor'

        def createBlockNode(nodes_array_index, block):
            idstr = 'bid_' + str( block.id )

            node = {}
            node['name'] = block.name
            node['type'] = 'block'

            node['tostr'] = block.toStr()
            node['id'] = idstr
            node['nodes_array_index'] = nodes_array_index

            return node, idstr


        def createSimulationInputNode(nodes_array_index, inSig):
            # append a node that stands for a simulation input
            idstr = 'insig_' + inSig.name

            node = {}
            node['name'] = 'in_' + inSig.name
            node['type'] = 'simulation_input'

            # node['tostr'] = block.toStr()
            node['id'] = idstr
            node['nodes_array_index'] = nodes_array_index

            return node, idstr

        def createLink(signal, sourceBlock, destBlock):
            # create a link in-between blocks

            link = {}
            link['tostr'] = signal.toStr()
            link['name'] = signal.name

            link['source'] = ''
            link['target'] = ''

            link['source_bid'] = sourceBlock.id
            link['target_bid'] = destBlock.id

            link['source_key'] = 'bid_' + str( sourceBlock.id )
            link['target_key'] = 'bid_' + str( destBlock.id )

            return link

        def createLinkFromSimulationInput(signal, destBlock):
            # create a link between a maker-node for the simulation input signal
            # anf the destination block 

            link = {}
            link['tostr'] = signal.toStr()
            link['name'] = signal.name

            link['source'] = ''
            link['target'] = ''

            link['target_bid'] = destBlock.id

            link['source_key'] = idstr
            link['target_key'] = 'bid_' + str( destBlock.id )

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
            if blk.getInputSignals() is not None and len( blk.getInputSignals() ) > 0:
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


    @property
    def blocks(self):
        return self.BlocksArray

    def GetInputInterface(self):
        # Build an input-interface for the ORTD interpreter
        # inform of a "inlist" structure

        print("external input signals:")
        
        for ExtInSig in self.ExternalConnectionsArray:
            ExtInSig.getDatatype().Show()

        return self.ExternalConnectionsArray


    def resolve_anonymous_signals(self, ignore_signals_with_datatype_inheritance=False):
        """
            close down the anonymous signals and wire the connected blocks directly to the source. 
        """
        
        for block in self.BlocksArray:
            block.verifyInputSignals(ignore_signals_with_datatype_inheritance)

    def propagate_datatypes(self):
        print("propagating datatypes...")

        self.resolve_anonymous_signals(ignore_signals_with_datatype_inheritance=True)

        # find out the output datatypes
        self.datatypePropagation.fixateTypes()


        # execute this later in the compilatin process

        # for block in self.BlocksArray:
        #     block.verifyInputSignals(ignore_signals_with_datatype_inheritance=False)

    @property
    def signal_with_unresolved_datatypes(self):
        return self.datatypePropagation.signalsWithUnderminedTypes


    

        










