from .signal_network.signals import *
from .signal_network.Block import *
from .datatype_propagation import *

from contextlib import contextmanager
from typing import Dict, List
from colorama import init,  Fore, Back, Style
init(autoreset=True)



class System:
    def __init__(self, upper_level_system, name : str ):

        self.upper_level_system = upper_level_system
        self._name = name
        self.blocks_in_system = []

        # counter for system input signals
        # This determines the order of teh arguments of the generated c++ functions
        self.simulation_input_signal_counter = 0

        self._top_level_system = None

        if upper_level_system is None:
            self._top_level_system = self

            self.block_id_counter = 0
            self.signal_id_counter = 0

            # manager to determine datatypes as new blocks are added
            # only for the highest-level system -- subsystems use the 
            # datatype propagation of the main system
            self.datatype_propagation_instance = DatatypePropagation(self)

        else:
            self._top_level_system = upper_level_system._top_level_system

            # # share the counter of the 
            # self.block_id_counter = upper_level_system.block_id_counter
            # self.signal_id_counter = upper_level_system.signal_id_counter

            # re-use the upper-level propagation
            self.datatype_propagation_instance = upper_level_system.datatype_propagation_instance

        # components
        self.components_ = {}

        # subsystems
        self._subsystems = []

        # primary outputs
        self._output_signals = []

        # signals that must be computed 
        self._signals_mandatory_to_compute = []

        # the results of the compilation of this system
        self.compile_result = None

    def getName(self):
        return self._name

    @property
    def name(self):
        return self._name

    @property
    def parent_system(self):
        return self.upper_level_system 

    def generate_new_block_id(self):
        self._top_level_system.block_id_counter += 1
        return self._top_level_system.block_id_counter

    # get a new unique id for creating a signal
    def generate_new_signal_id(self):
        self._top_level_system.signal_id_counter += 1
        return self._top_level_system.signal_id_counter

    def append_subsystem(self, system):
        """
            add a subsystem to the list of subsystems to this system
        """
        self._subsystems.append( system )

    @property
    def subsystems(self):
        return self._subsystems

    def addBlock(self, blk : Block):
        self.blocks_in_system.append(blk)

    # TODO: remove this?
    def set_primary_outputs(self, outputSignals):
        self._output_signals = outputSignals

    def append_output(self, outputSignals):
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

        for blk in self.blocks_in_system:
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
        # TODO: remove from this class and move to an other class 'visualization' or 'editor'

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
        for block in self.blocks_in_system:

            node, idstr = createBlockNode(nodes_array_index, block)

            nodes_array.append( node )
            nodes_hash[idstr] = node

            nodes_array_index += 1

        
        # build links
        for blk in self.blocks_in_system:

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
        return self.blocks_in_system

    def resolve_anonymous_signals(self, ignore_signals_with_datatype_inheritance=False):
        """
            close down the anonymous signals and wire the connected blocks directly to the source. 
        """
        
        for block in self.blocks_in_system:
            block.verifyInputSignals(ignore_signals_with_datatype_inheritance)

    def propagate_datatypes(self):
        self.resolve_anonymous_signals(ignore_signals_with_datatype_inheritance=True)

        # find out the output datatypes
        self.datatype_propagation_instance.fixateTypes()


        # execute this later in the compilatin process

        # for block in self.blocks_in_system:
        #     block.verifyInputSignals(ignore_signals_with_datatype_inheritance=False)

    @property
    def signal_with_unresolved_datatypes(self):
        return self.datatype_propagation_instance.signalsWithUnderminedTypes


    

        










