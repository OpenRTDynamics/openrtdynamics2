from . import libdyn

from . import CompileDiagram as cd
from . import SignalInterface as si

from .CodeGenTemplates import *
from .system_context import *
from .BlockPrototypes import *
from .StandardLibrary import *
from .subsystems import *

import json
import os


def signal():
    # return an anonymous signal
    return si.SignalUser(get_simulation_context())

def system_input(datatype):
    # intoduce a system input 
    return si.SimulationInputSignalUser(get_simulation_context(), datatype)
    

def export_graph(filename, system = None):

    if system is None:
        system = get_simulation_context() 


    # filename = 'generated/graph.json'

    print()
    print(Style.BRIGHT + "-------- export graph --------")
    print()

    graph = system.exportGraph()

    with open( os.path.join(  filename ), 'w') as outfile:  
        json.dump(graph, outfile)

def show_blocks(system = None):

    if system is None:
        system = get_simulation_context() 

    print()
    print(Style.BRIGHT + "-------- list of blocks --------")
    print()

    system.ShowBlocks()

def compile_system(system = None):

    if system is None:
        system = get_simulation_context() 

    print()
    print(Style.BRIGHT + "-------- Compile connections (determine datatypes) --------")
    print()

    system.propagate_datatypes()



    #
    # compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
    # at runtime.
    #

    compiler = cd.CompileDiagram()
    comileResults = compiler.compile( system )

    #
    return comileResults

def compile_current_system():
    return compile_system( get_simulation_context() )


def show_execution_lines(compile_results):

    print()
    print(Style.BRIGHT + "-------- List all execution lines and commands  --------")
    print()

    compile_results.commandToExecute.printExecution()
