from . import libdyn
from . import diagram_compiler as cd
from . import signal_interface as si

from .code_generation_templates import PutRuntimeCppHelper, PutBasicRuntimeCpp, WasmRuntime

from .system_context import *
from .standard_library import *
from .subsystems import *

import os
from pathlib import Path


def signal():
    """
        Create a new signal for defining a closed-loop
    """

    # return an anonymous signal
    return si.SignalUser(get_simulation_context())



def system_input(datatype, name : str = None, default_value=None, value_range=None, title : str = ""):
    """
        Introduce a new system input signal

        datatype      - the datatype of the signal
        name          - the name of the signal
        default_value - the default value the will be applied to the system input by default
        value_range   - the available numeric range for the signal the form [min, max]  
        title         - the description of the signal
    """

    signal = si.SimulationInputSignalUser(get_simulation_context(), datatype)

    if name is not None:
        signal.set_name(name)

    properties = {}

    if default_value is not None:
        properties['default_value'] = default_value

    if value_range is not None:
        properties['range'] = value_range

    if title is not None:
        properties['title'] = title

    signal.set_properties(properties)

    return signal 


def export_graph(filename, system = None):

    if system is None:
        system = get_simulation_context() 

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

    compile_results.command_to_execute.print_execution()





def generate_code(template : PutRuntimeCppHelper, folder=None, build=False):

    # Compile system (propagate datatypes)
    compile_results = dy.compile_current_system()

    # Build an executable based on a template
    template.set_compile_results( compile_results )
    code_gen_results = template.code_gen()

    if folder is not None:

        # check of path exists - in case no, create it
        Path(folder).mkdir(parents=True, exist_ok=True)

        print("Generated code will be written to " + str(folder) + ' .')

        # write generated code into a folder and build
        template.write_code(folder)

        if build:
            template.build()


    return code_gen_results
