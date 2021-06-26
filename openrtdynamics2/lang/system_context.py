from .diagram_core.system import System
from typing import Dict, List
from . import signal_interface as si

class _SystemContext:
    """
        internal class to store information about the system
    """
    def __init__(self):
        self.current_system = None
        self.system_stack = []
        self.counter_of_created_systems = 1000
        self.list_of_code_sources = {}

        self.main_system_inputs_signals = []

    def append_main_system_input(self, signal : si.SimulationInputSignalUser):
        self.main_system_inputs_signals.append(signal)

def init_simulation_context():
    global _system_context
    _system_context = _SystemContext()



_system_context = None
init_simulation_context()








def push_simulation_context(system):

    global _system_context
    _system_context.current_system = system
    _system_context.system_stack.append(system)


def pop_simulation_context():

    global _system_context

    old_context = _system_context.system_stack.pop()

    if not len(_system_context.system_stack) == 0:
        new_context = _system_context.system_stack[-1]
    else:
        new_context = None

    _system_context.current_system = new_context

    return new_context

def get_current_system():
    global _system_context
    return _system_context.current_system


def get_system_context():
    global _system_context
    return _system_context


def generate_subsystem_name():
    """
        automatically created a unique name for a system
    """
    # global counter_of_created_systems
    global _system_context

    name = 'Sys' + str(_system_context.counter_of_created_systems)
    _system_context.counter_of_created_systems += 1

    return name

def enter_system(name : str = 'simulation', upper_level_system = None):
    """
        create a new system and activate it in the context
    """
    # new simulation
    system = System(upper_level_system, name)

    # register this subsystem to the parent system
    if get_current_system() is not None:
        get_current_system().append_subsystem( system )

    push_simulation_context(system)

    return system

def enter_subsystem(name : str):
    """
        create a new subsystem in the current system context and activate it in the context
    """
    return enter_system(name, get_current_system())

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

    get_current_system().set_primary_outputs( si.unwrap_list( output_signals ) )


def append_output(output_signal, export_name : str = None):
    """
        add an output to the current system

        output_signal: SignalUserTemplate, structure
            either a signal of type 
        export_name: str
            name of the signal or prefix of the names of the signals in the structure
    """

    if isinstance(output_signal, si.SignalUserTemplate ): 

        # set name
        if export_name is not None:
            output_signal.set_name_raw(export_name)

        # add to outputs
        get_current_system().append_output(output_signal.unwrap)

    elif isinstance(output_signal, si.structure ):

        for name, signal in output_signal.items():

            # set name
            if export_name is not None:
                # use export_name as a prefix
                signal.set_name_raw( export_name + '_' + name )
            else:
                signal.set_name_raw( name )

            # add to outputs
            get_current_system().append_output(signal.unwrap)


def include_cpp_code(
        identifier : str,
        code : str = None,
        include_files : List[str] = None,
        library_names : List[str] = None
    ):

    """
    Include the given c++ source code into the code generation process
    """

    global _system_context

    _system_context.list_of_code_sources[identifier] = { 
        'code' : code, 
        'include_files' : include_files, 
        'library_names' : library_names 
    }

def get_list_of_code_sources():
    global _system_context
    return _system_context.list_of_code_sources
