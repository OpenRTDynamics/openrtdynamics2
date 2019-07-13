from libdyn import *
from Signal import *
from Block import *
from BlockPrototypes import *

from SimulationContext import *


print("-- RTDynamics II loaded --")

def signal():
    return Signal(get_simulation_context())

def system_input(datatype):
    return SimulationInputSignal(get_simulation_context(), datatype)
    
