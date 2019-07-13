from libdyn import *
from Signal import *
# from Block import *
# from BlockPrototypes import *


current_simulation_context = None

simulation_stack = []

def push_simulation_context(sim):
    global current_simulation_context

    current_simulation_context = sim

    global simulation_stack
    simulation_stack.append(sim)

def pop_simulation_context():
    global simulation_stack
    simulation_stack.pop()


def get_simulation_context():
    return current_simulation_context



def enter_system(name : str):
    # new simulation
    sim = Simulation(None, 'main')

    push_simulation_context(sim)

    return sim
