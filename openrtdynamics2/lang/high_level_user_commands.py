from .diagram_core import diagram_compiler as dc
from . import signal_interface as si
from .code_generation_templates import TargetGenericCpp
from .system_context import init_simulation_context, get_current_system, get_system_context, enter_system, leave_system, clear, set_primary_outputs, append_output, get_list_of_code_sources

import os
import pathlib as pl
import typing as t
from colorama import init,  Fore, Back, Style
init(autoreset=True)




def signal():
    """
        Create a new signal for defining a closed-loop
    """

    # return an anonymous signal
    return si.SignalUser(get_current_system())



def system_input(datatype, name : str = None, default_value=None, value_range=None, title : str = ""):
    """
        Introduce a new system input signal

        datatype      - the datatype of the signal
        name          - the name of the signal
        default_value - the default value the will be applied to the system input by default
        value_range   - the available numeric range for the signal the form [min, max]  
        title         - the description of the signal
    """

    signal = si.SimulationInputSignalUser(get_current_system(), datatype)

    if get_current_system().upper_level_system is not None:
        raise BaseException('system_input() is not available for subsystems')

    get_system_context().append_main_system_input( signal )

    #
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
        system = get_current_system() 

    graph = system.exportGraph()

    with open( os.path.join(  filename ), 'w') as outfile:  
        json.dump(graph, outfile)

def show_blocks(system = None):
    """
        List all blocks in the current or given system
    """

    if system is None:
        system = get_current_system() 

    print()
    print(Style.BRIGHT + "-------- list of blocks --------")
    print()

    system.ShowBlocks()

def compile_system(system = None):

    if system is None:
        system = get_current_system() 

    system.propagate_datatypes()

    #
    # compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
    # at runtime.
    #

    compiler = dc.CompileDiagram()
    compile_results = compiler.compile( 
        system, 
        input_signals =  si.unwrap_list( get_system_context().main_system_inputs_signals )
    )

    #
    return compile_results


def show_execution_lines(compile_results):

    print()
    print(Style.BRIGHT + "-------- List all execution lines and commands  --------")
    print()

    # TODO: seems broken needs update 21.3.2021

    compile_results.command_to_execute.print_execution()


def generate_code(template : TargetGenericCpp, folder=None, build=False, list_of_code_sources = {} ):
    """
    Generate code from the current system given a template
    """

    # get includes
    template.add_code_to_include(list_of_code_sources)

    # includes that were specified by the command 'dy.include_cpp_code'
    template.add_code_to_include(get_list_of_code_sources())


    # Compile system (propagate datatypes)
    compile_results = compile_system()

    # Build an executable based on a template
    template.set_compile_results( compile_results )
    code_gen_results = template.code_gen()

    if folder is not None:

        # check of path exists - in case no, create it
        pl.Path(folder).mkdir(parents=True, exist_ok=True)

        print("Generated code will be written to " + str(folder) + ' .')

        # write generated code into a folder and build
        template.write_code(folder)

        if build:
            template.build()


    return code_gen_results
