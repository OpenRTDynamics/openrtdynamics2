from libdyn import *
from Signal import *
# from Block import *
# from BlockPrototypes import *


current_simulation_context = None
simulation_stack = []

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



def enter_system(name : str):
    # new simulation
    sim = Simulation(None, name)

    print("enter_system: created " + str(sim) )

    push_simulation_context(sim)

    return sim

def leave_system():
    return pop_simulation_context()
