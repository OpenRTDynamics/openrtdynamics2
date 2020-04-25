from . import libdyn


#from . import Signal
#from . import Block
#from Block import *
#from . import ExecutionCommands

# from . import SystemLibrary

from . import CompileDiagram as cd
from . import SignalInterface as si

from .CodeGenTemplates import *
from .system_context import *
from .BlockPrototypes import *
from .StandardLibrary import *
from .subsystems import *

import json
import os

print("-- RTDynamics II loaded --")

def signal():
    # return an anonymous signal
    return si.SignalUser(get_simulation_context())

def system_input(datatype):
    # intoduce a system input 
    return si.SimulationInputSignalUser(get_simulation_context(), datatype)
    

def compile_system(sim):

    # sim.ShowBlocks()

    print()
    print(Style.BRIGHT + "-------- Compile connections (determine datatypes) --------")
    print()

    sim.propagate_datatypes()

    print()
    print(Style.BRIGHT + "-------- print datatypes --------")
    print()

    sim.ShowBlocks()

    print()
    print(Style.BRIGHT + "-------- export graph --------")
    print()

    graph = sim.exportGraph()

    with open( os.path.join(  'generated/graph.json' ), 'w') as outfile:  
        json.dump(graph, outfile)

    #
    # compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
    # at runtime.
    #

    compiler = cd.CompileDiagram()
    comileResults = compiler.compile( sim )

    #
    return comileResults

def compile_current_system():
    return compile_system( get_simulation_context() )