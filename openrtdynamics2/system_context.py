from .libdyn import *
#from Signal import *
from . import SignalInterface as si


current_simulation_context = None
simulation_stack = []

counter_of_created_systems = 1000

def generate_subsystem_name():
    """
        automatically created unique name for a system
    """
    global counter_of_created_systems

    name = 'Subsystem' + str(counter_of_created_systems)
    counter_of_created_systems += 1

    return name



def push_simulation_context(sim):
    global simulation_stack
    global current_simulation_context

    current_simulation_context = sim
    simulation_stack.append(sim)

def pop_simulation_context():
    global simulation_stack
    global current_simulation_context

    old_context = simulation_stack.pop()

    if not len(simulation_stack) == 0:
        new_context = simulation_stack[-1]
    else:
        new_context = None

    current_simulation_context = new_context

    return new_context


def get_simulation_context():
    global current_simulation_context
    return current_simulation_context

def enter_system(name : str, upper_level_system = None):
    """
        create a new system
    """
    # new simulation
    system = Simulation(upper_level_system, name)

    # register this subsystem to the parent system
    if get_simulation_context() is not None:
        get_simulation_context().appendNestedSystem( system )

    print("enter_system: created " + str(system) )

    push_simulation_context(system)

    return system

def enter_subsystem(name : str):
    """
        create a new subsystem in the current system context
    """
    return enter_system(name, get_simulation_context())

def leave_system():
    return pop_simulation_context()


def set_primary_outputs(output_signals):
    get_simulation_context().set_primary_outputs( si.unwrap_list( output_signals ) )
