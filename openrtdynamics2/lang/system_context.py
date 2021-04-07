from .diagram_core.system import System
from typing import Dict, List
from . import signal_interface as si


current_simulation_context = None
system_stack = []
counter_of_created_systems = 1000
list_of_code_sources = {}

def init_simulation_context():
    global system_stack
    global current_simulation_context
    global counter_of_created_systems
    global list_of_code_sources

    current_simulation_context = None
    system_stack = []
    counter_of_created_systems = 1000
    list_of_code_sources = {}

def push_simulation_context(sim):
    global system_stack
    global current_simulation_context

    current_simulation_context = sim
    system_stack.append(sim)

def pop_simulation_context():
    global system_stack
    global current_simulation_context

    old_context = system_stack.pop()

    if not len(system_stack) == 0:
        new_context = system_stack[-1]
    else:
        new_context = None

    current_simulation_context = new_context

    return new_context

def get_system_context():
    global current_simulation_context
    return current_simulation_context


def generate_subsystem_name():
    """
        automatically created a unique name for a system
    """
    global counter_of_created_systems

    name = 'Subsystem' + str(counter_of_created_systems)
    counter_of_created_systems += 1

    return name

def enter_system(name : str = 'simulation', upper_level_system = None):
    """
        create a new system and activate it in the context
    """
    # new simulation
    system = System(upper_level_system, name)

    # register this subsystem to the parent system
    if get_system_context() is not None:
        get_system_context().append_subsystem( system )

    push_simulation_context(system)

    return system

def enter_subsystem(name : str):
    """
        create a new subsystem in the current system context and activate it in the context
    """
    return enter_system(name, get_system_context())

def leave_system():
    return pop_simulation_context()

def clear():
    """
        clear the context
    """
    init_simulation_context()

def set_primary_outputs(output_signals, names = None):

    if names is not None:
        for i in range(0,len(names)):
            output_signals[i].set_name_raw( names[i] )

    get_system_context().set_primary_outputs( si.unwrap_list( output_signals ) )

def append_output(output_signal, export_name : str = None):
    """
        add an output to the current system
    """

    if export_name is not None:
        output_signal.set_name_raw(export_name)

    get_system_context().append_output(output_signal.unwrap)
    
def include_cpp_code(identifier : str, code : str = None, include_files : List[str] = None, library_names : List[str] = None):
    """
    Include the given c++ source code into the code generation process
    """

    global list_of_code_sources

    list_of_code_sources[identifier] = { 
        'code' : code, 
        'include_files' : include_files, 
        'library_names' : library_names 
    }

def get_list_of_code_sources():
    global list_of_code_sources
    return list_of_code_sources
