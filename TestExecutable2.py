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



datatype = DataTypeFloat(1) 
#datatype = DataTypeInt32(1) 


#U = dyn_const(sim, 1.123, datatype ).setNameOfOrigin('U (const)').setName('U')
U = SimulationInputSignal(sim, port=0, datatype=DataTypeFloat(1) ).setName('extU')



# y = firstOrder(sim, U, 0.2, name="1")
# y = firstOrder(sim, y, 0.2, name="2")
# y = firstOrder(sim, y, 0.2, name="3")

y1 = firstOrderAndGain(sim, U, 0.2, gain=0.8, name="1")
y2 = firstOrderAndGain(sim, y1, 0.2, gain=0.8, name="2")
y3 = firstOrderAndGain(sim, y2, 0.2, gain=0.8, name="3")


E = SimulationInputSignal(sim, port=0, datatype=DataTypeFloat(1) ).setName('extE')

y = dyn_add(sim, [ y3, E ], [ 1, 1 ] ).setNameOfOrigin('y (add)').setName('y')

# define the outputs of the simulation
outputSignals = [ y, y2 ]

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
print(Style.BRIGHT + "-------- Find dependencies for calcularing the outputs  --------")
print()




# collect all execution lines with:
executionLineToCalculateOutputs = ExecutionLine( [], [] )

# for all requested output singals
for s in outputSignals:
    elForOutputS = E.getExecutionLine( s )
    elForOutputS.printExecutionLine()

    # merge all lines into one
    executionLineToCalculateOutputs.appendExecutionLine( elForOutputS )




print()
print(Style.BRIGHT + "-------- Build all execution paths  --------")
print()

# look into executionLineToCalculateOutputs.dependencySignals and use E.getExecutionLine( ) for each
# element. Also collect the newly appearing dependency signals in a list and also 
# call E.getExecutionLine( ) on them. Stop until no further dependend signal appear.
# finally concatenare the execution lines

# 

# start with following signals to be computed
dependencySignals = executionLineToCalculateOutputs.dependencySignals

# get the simulation-input signals in dependencySignals
# NOTE: these are only the simulation inputs that are needed to calculate the output y
simulationInputSignalsForCalcOutputs = []
for s in dependencySignals:
    if isinstance(s, SimulationInputSignal):
        simulationInputSignalsForCalcOutputs.append(s)

# counter for the order (i.e. step through all delays present in the system)
order = 0



# execution line per order
commandToCalcTheResultsToPublish = CommandCalculateOutputs(executionLineToCalculateOutputs, outputSignals)

# cache all signals that are calculated so far
commandToCacheIntermediateResults = CommandCacheOutputs( executionLineToCalculateOutputs.signalOrder )

# build the function calcPrimaryResults() that calculates the outputs of the simulation.
# Further, it stores intermediate results
commandToPublishTheResults = PutAPIFunction("calcResults_1", 
                                            inputSignals=simulationInputSignalsForCalcOutputs,   # TODO: only add the elements that are inputs
                                            outputSignals=outputSignals, 
                                            executionCommands=[ commandToCalcTheResultsToPublish, commandToCacheIntermediateResults ] )

# Initialize the list of commands to execute to update the states
commandsToExecuteForStateUpdate = []

# the simulation intputs needed to perform the state update
simulationInputSignalsForStateUpdate = []

while True:

    print("--------- Computing order "+ str(order) + " --------")
    print("dependent sources:")
        
    for s in dependencySignals:
        print(Fore.YELLOW + "  - " + s.toStr() )


    # do for each dependency Signal in the list
    # nextOrderDependencySingals = []

    # collect all executions lines build in this order
    executionLinesForCurrentOrder = []

    # backwards jump over the blocks that compute dependencySignals through their states
    # result is dependencySignals__ which are the inputs to these blocks
    print(Style.DIM + "These sources are translated to (through their blocks via state-update):")

    dependencySignals__ = []
    for s in dependencySignals:

        # find out which signals are needed to calculate the states needed to calculate dependencySignals
        # returnInutsToUpdateStates

        if isinstance(s, SimulationInputSignal):
            simulationInputSignalsForStateUpdate.append(s)

        else:  # TODO: if isinstance(s, BlockOutputSignal):
            for s_ in s.getSourceBlock().getBlockPrototype().returnInutsToUpdateStates( s ):

                print(Fore.YELLOW + Style.BRIGHT + "  - " + s_.toStr() )

                # only append of this signals is not already computable
                if not E.isSignalAlreadyComputable(s_):
                    dependencySignals__.append(s_)

                else:
                    print(Style.DIM + "    This signal is already computable (no futher execution line is calculated to this signal)")


    # create executionline for calculating the dependency singlas and at the end of the overall line
    #executionLineForS_finalStep = ExecutionLine( dependencySignals__ )

    
    for s in dependencySignals__:

        # get execution line to calculate s
        executionLineForS = E.getExecutionLine(s)  # verified: s is also included in the execution line

        #print('  - - - the line for signal - - - ' + s.toStr() )
        #executionLineForS.printExecutionLine()    # also here: s is part of the line

        # store this execution line
        executionLinesForCurrentOrder.append(executionLineForS)

        # collect all newly appearing dependency signals 
        # found in executionLineForS.dependencySignals
        # nextOrderDependencySingals.extend( executionLineForS.dependencySignals )


    # merge all lines into one
    executionLineForCurrentOrder = ExecutionLine( [], [] )

    #

    #
    for e in executionLinesForCurrentOrder:

        # append execution line
        executionLineForCurrentOrder.appendExecutionLine( e )



    #print('  - - - the line for this order - - - '  )
    #executionLineForCurrentOrder.printExecutionLine()



    # collect executionLineForCurrentOrder
    commandsToExecuteForStateUpdate.append( CommandCalculateOutputs(executionLineForCurrentOrder, dependencySignals__) )

    # generate state update commands for the blocks that have dependencySignals as outputs
    # TODO: This is new and unchecked
    print("state update of blocks connected to:")

    blocksWhoseStatesToUpdate = []
    for s in dependencySignals:
        #print("  - " + s.toStr())
        
        
        #  TODO: use: if isinstance(s, BlockOutputSignal):
        if not isinstance(s, SimulationInputSignal):
            # s is a signal that comes from a block
            blocksWhoseStatesToUpdate.append( s.getSourceBlock() )

        if isinstance(s, SimulationInputSignal):
            # append this signals s to the list of needed simulation inputs
            # TODO: investigate if this is really needed and does not produce double appends to the list
            # simulationInputSignalsForStateUpdate.append(s)

            pass

    sUpCmd = CommandUpdateStates( blocksWhoseStatesToUpdate)

    commandsToExecuteForStateUpdate.append( sUpCmd )

    #print("added command(s) to perform state update:")
    #sUpCmd.printExecution()

    # get the dependendy singals of the current order
    dependencySignals = executionLineForCurrentOrder.dependencySignals

    # iterate
    #dependencySignals = nextOrderDependencySingals  # guess... ????
    order = order + 1
    if len(dependencySignals) == 0:
        print(Fore.GREEN + "All dependencies are resolved")

        break

    if order == 30:
        break


# Build API to update the states: e.g. c++ function updateStates()
commandToUpdateStates = PutAPIFunction( nameAPI = 'updateStates', 
                                        inputSignals=simulationInputSignalsForStateUpdate, 
                                        outputSignals=[], 
                                        executionCommands=commandsToExecuteForStateUpdate )



# build the program
commandsToExecute = [ commandToPublishTheResults, 
                      commandToUpdateStates  ]



#
# List all execution lists
#

print()
print(Style.BRIGHT + "-------- List all execution commands  --------")
print()

for command in commandsToExecute:
    command.printExecution()





print()
print(Style.BRIGHT + "-------- Code generation  --------")
print()

sourcecode = ''
sourcecode += "class compiledSimulation {\n\n"

#
# define member variables
#

# TODO: use an API function and a execution command to set the initial values

sourcecode += "// state variables\n"

for block in sim.getBlocksArray():
    sourcecode += block.getBlockPrototype().codeGen('c++', 'defStates')


# generate the member variables by calling 'variables'
sourcecode += "\n\n// cached output values\n"
sourcecode += commandToPublishTheResults.codeGen('c++', 'variables')

# generate the member variables by calling 'variables'
sourcecode += "\n\n// state update\n"
sourcecode += commandToUpdateStates.codeGen('c++', 'variables')


# # generate the member variables by calling 'variables'
# # general function build command -- but to complex to be easiely understandable
#
# for command in commandsToExecute:
#     sourcecode += command.codeGen('c++', 'variables')

#
# generate reset()
#

# TODO: use an API function and a execution command to set the initial values

sourcecode += "\n// reset the states of the stimulation\n"
sourcecode += "void reset() {\n"

for block in sim.getBlocksArray():
    sourcecode += block.getBlockPrototype().codeGen('c++', 'reset')

sourcecode += "} // reset\n"


# Update
sourcecode += "\n//\n// autogenerated functions\n//\n\n"

# general function build command -- but to complex to be easiely understandable
# for command in commandsToExecute:
#     sourcecode += command.codeGen('c++', 'code')


# # generate calcPrimaryResults()
sourcecode += "\n\n// cached output values\n"
sourcecode += commandToPublishTheResults.codeGen('c++', 'code')

# # generate updateStates()
sourcecode += "\n\n// state update\n"
sourcecode += commandToUpdateStates.codeGen('c++', 'code')


sourcecode += "\n};\n"


print(Style.DIM + sourcecode)
print()

# finish
#sim.export_ortdrun('RTMain')
#sim.ShowBlocks()











