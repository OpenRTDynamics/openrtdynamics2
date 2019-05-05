from libdyn import *
from irpar import *
from BlockPrototypes import *
from TraverseGraph import *
from Signal import *
from ExecutionCommands import *

from colorama import init,  Fore, Back, Style
init(autoreset=True)



# new simulation
sim = Simulation(None, 'main')




#

def firstOrder(sim, u, z_inf, name):

    yFb = Signal(sim)

    i = dyn_add(sim, [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dyn_delay(sim, i).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb.setequal( y )

    return y


def firstOrderAndGain(sim, u, z_inf, gain, name):

    yFb = Signal(sim)

    s = dyn_add(sim, [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_s (add)').setName('s'+name+'')
    d = dyn_delay(sim, s).setNameOfOrigin(name + '_d (delay)').setName('d'+name+'')
    y = dyn_gain(sim, d, gain).setNameOfOrigin(name + '_y (gain)').setName('y'+name+'')

    yFb.setequal( y )

    return y

U = dyn_const(sim, 1.123).setNameOfOrigin('U (const)').setName('U')



# y = firstOrder(sim, U, 0.2, name="1")
# y = firstOrder(sim, y, 0.2, name="2")
# y = firstOrder(sim, y, 0.2, name="3")

y = firstOrderAndGain(sim, U, 0.2, gain=0.8, name="1")
y = firstOrderAndGain(sim, y, 0.2, gain=0.8, name="2")
y = firstOrderAndGain(sim, y, 0.2, gain=0.8, name="3")




# test 
sim.ShowBlocks()



print()
print(Style.BRIGHT + "-------- Compile connections --------")
print()
sim.CompileConnections()

print()
print(Style.BRIGHT + "-------- print datatypes --------")
print()

sim.ShowBlocks()

#
# create execution path builder
#
E=BuildExecutionPath()


print()
print(Style.BRIGHT + "-------- Find dependencies for calcularing 'y'  --------")
print()

executionLine1 = E.getExecutionLine( y )
executionLine1.printExecutionLine()

print()
print(Style.BRIGHT + "-------- Build all execution paths  --------")
print()

# look into executionLine1.dependencySignals and use E.getExecutionLine( ) for each
# element. Also collect the newly appearing dependency signals in a list and also 
# call E.getExecutionLine( ) on them. Stop until no further dependend signal appear.
# finally concatenare the execution lines

# 

# start with following signals to be computed
dependencySignals = executionLine1.dependencySignals

# counter for the order (i.e. step through all delays present in the system)
order = 0



# execution line per order
commandToCalcTheResultsToPublish = CommandCalculateOutputs(executionLine1, [ y ])

commandToPublishTheResults = CommandPublishResult(y, commandToCalcTheResultsToPublish )

# Initialize the list of commands to execute to update the states
commandsToExecuteForStateUpdate = []

while True:

    print("--------- Comuting order "+ str(order) + " --------")
    print("dependent sources:")
        
    for s in dependencySignals:
        print(Fore.YELLOW + "  - " + s.toStr() )


    # do for each dependency Signal in the list
    nextOrderDependencySingals = []

    # collect all executions lines build in this order
    executionLinesForCurrentOrder = []

    # backwards jump over the blocks that compute dependencySignals through their states
    # result is dependencySignals__ which are the inputs to these blocks
    print(Style.DIM + "These sources are translated to (through their blocks via state-update):")

    dependencySignals__ = []
    for s in dependencySignals:

        # find out which signals are needed to calculate the states needed to calculate dependencySignals
        # returnInutsToUpdateStates

        for s_ in s.getSourceBlock().getBlockPrototype().returnInutsToUpdateStates( s ):

            print(Fore.YELLOW + Style.BRIGHT + "  - " + s_.toStr() )

            # only append of this signals is not already computable
            if not E.isSignalAlreadyComputable(s_):
                dependencySignals__.append(s_)

            else:
                print(Style.DIM + "    This signal is already computable (no futher execution line is calculated to this signal)")



    
    for s in dependencySignals__:

        # get execution line to calculate s
        executionLineForS = E.getExecutionLine(s)

        # store this execution line
        executionLinesForCurrentOrder.append(executionLineForS)

        # collect all newly appearing dependency signals 
        # found in executionLineForS.dependencySignals
        nextOrderDependencySingals.extend( executionLineForS.dependencySignals )


    # merge all lines into one
    executionLineForCurrentOrder = ExecutionLine( [], [] )
    for e in executionLinesForCurrentOrder:

        # append execution line
        executionLineForCurrentOrder.appendExecutionLine( e )

    # collect executionLineForCurrentOrder
    commandsToExecuteForStateUpdate.append( CommandCalculateOutputs(executionLineForCurrentOrder, dependencySignals__) )

    # get the dependendy singals of the current order
    dependencySignals = executionLineForCurrentOrder.dependencySignals


    # generate state update commands for the blocks that have dependencySignals as outputs
    # TODO: This is new and unchecked
    blocksWhoseStatesToUpdate = []
    for s in dependencySignals:
        blocksWhoseStatesToUpdate.append( s.getSourceBlock() )

    commandsToExecuteForStateUpdate.append( CommandUpdateStates( blocksWhoseStatesToUpdate) )


    # iterate
    order = order + 1
    if len(dependencySignals) == 0:
        print(Fore.GREEN + "All dependencies are resolved")

        break

    if order == 30:
        break



commandsToExecute = [ commandToPublishTheResults, CommandCompondUpdateStates( commandsToExecuteForStateUpdate )  ]



#
# List all execution lists
#

print()
print(Style.BRIGHT + "-------- List all execution commands  --------")
print()

for command in commandsToExecute:

    command.printExecution()


    pass



print()
print(Style.BRIGHT + "-------- Code generation  --------")
print()

sourcecode = ''

sourcecode += "class compiledSimulation {\n\n"

sourcecode += "// state variables\n"

for block in sim.getBlocksArray():
    sourcecode += block.getBlockPrototype().codeGen('c++', 'defStates')

sourcecode += "\n// reset the states of the stimulation\n"
sourcecode += "void reset() {\n"

for block in sim.getBlocksArray():
    sourcecode += block.getBlockPrototype().codeGen('c++', 'reset')

sourcecode += "} // reset\n"


# Update

sourcecode += "\n//\n// autogenerated functions\n//\n"


for command in commandsToExecute:

    sourcecode += command.codeGen('c++', 'begin')
    sourcecode += command.codeGen('c++', 'end')

sourcecode += "\n};\n"


print(Style.DIM + sourcecode)
print()

# finish
#sim.export_ortdrun('RTMain')
#sim.ShowBlocks()











