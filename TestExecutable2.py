from libdyn import *
from BlockPrototypes import *
from Signal import *
from ExecutionCommands import *
from CodeGenTemplates import *
from CompileDiagram import *

from colorama import init,  Fore, Back, Style
init(autoreset=True)


# new simulation
sim = Simulation(None, 'main')


def firstOrder(sim, u : Signal, z_inf, name : str):

    yFb = Signal(sim)

    i = dyn_add(sim, [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dyn_delay(sim, i).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb.setequal( y )

    # inherit datatype
    #i.setDatatype( u.getDatatype() )
    #s.deriveDatatypeFrom(u)

    return y


def firstOrderAndGain(sim, u : Signal, z_inf, gain, name : str):

    yFb = Signal(sim)

    s = dyn_add(sim, [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_s (add)').setName('s'+name+'')
    d = dyn_delay(sim, s).setNameOfOrigin(name + '_d (delay)').setName('d'+name+'')
    y = dyn_gain(sim, d, gain).setNameOfOrigin(name + '_y (gain)').setName('y'+name+'')

    yFb.setequal( y )

    return y



baseDatatype = DataTypeFloat(1) 
# baseDatatype = DataTypeInt32(1) 


#U = dyn_const(sim, 1.123, baseDatatype ).setNameOfOrigin('U (const)').setName('U')
U = SimulationInputSignal(sim, port=0, datatype=baseDatatype ).setName('extU')



# y = firstOrder(sim, U, 0.2, name="1")
# y = firstOrder(sim, y, 0.2, name="2")
# y = firstOrder(sim, y, 0.2, name="3")

y1 = firstOrderAndGain(sim, U, 0.2, gain=0.8, name="1")
y2 = firstOrderAndGain(sim, y1, 0.2, gain=0.8, name="2")
y3 = firstOrderAndGain(sim, y2, 0.2, gain=0.8, name="3")


E1 = SimulationInputSignal(sim, port=0, datatype=baseDatatype ).setName('extE1')
E2 = SimulationInputSignal(sim, port=0, datatype=baseDatatype ).setName('extE2')

y = dyn_add(sim, [ y3, E1, E2 ], [ 0.1, 0.2, 0.3] ).setNameOfOrigin('y (add)').setName('y')

# define the outputs of the simulation
outputSignals = [ y, y2 ]

# test 
sim.ShowBlocks()





print()
print(Style.BRIGHT + "-------- Compile connections (determine datatypes) --------")
print()
sim.CompileConnections()

print()
print(Style.BRIGHT + "-------- print datatypes --------")
print()

sim.ShowBlocks()

#
# compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
# at runtime.
#

compiler = CompileDiagram()
commandToExecute = compiler.compile( sim, outputSignals )


#
# Build an executable based on a template
#

# specify what the input signals shall be in the runtime
inputSignalsMapping = {}
inputSignalsMapping[ U ] = 1.0
inputSignalsMapping[ E1 ] = 2.0
inputSignalsMapping[ E2 ] = 3.0

runtimeCodeTemplate = PutBasicRuntimeCpp(commandToExecute, inputSignalsMapping=inputSignalsMapping)

#
# list all execution lists
#

print()
print(Style.BRIGHT + "-------- List all execution commands  --------")
print()

commandToExecute.printExecution()

#
# generate c++ cpde
#

print()
print(Style.BRIGHT + "-------- Code generation  --------")
print()

sourcecode = runtimeCodeTemplate.codeGen(iMax = 20)


print(Style.DIM + sourcecode)
print()



f = open("generated/simulation.cpp", "w")
f.write( sourcecode )
f.close()










