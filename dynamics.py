from libdyn import *
from Signal import *
from Block import *
from BlockPrototypes import *
from ExecutionCommands import *
from CodeGenTemplates import *
from CompileDiagram import *
from SimulationContext import *
from CompileDiagram import *
from SignalInterface import *
from SystemLibrary import *

from StandardLibrary import *

print("-- RTDynamics II loaded --")

def signal():
    # return an anonymous signal
    return SignalUser(get_simulation_context())

def system_input(datatype):
    # intoduce a system input 
    return SimulationInputSignalUser(get_simulation_context(), datatype)
    

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

    compiler = CompileDiagram()
    comileResults = compiler.compile( sim )

    #
    return comileResults

def compile_current_system():
    return compile_system( get_simulation_context() )