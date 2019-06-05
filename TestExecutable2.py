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
print(Style.BRIGHT + "-------- Compile connections --------")
print()
sim.CompileConnections()

print()
print(Style.BRIGHT + "-------- print datatypes --------")
print()

sim.ShowBlocks()


# exit()




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
commandToCalcTheResultsToPublish = CommandCalculateOutputs(executionLineToCalculateOutputs, outputSignals, defineVarsForOutputs = True)

#
# cache all signals that are calculated so far
# TODO: make a one-liner e.g.  signalsToCache = removeInputSignals( executionLineToCalculateOutputs.signalOrder )
#

signalsToCache = []
for s in executionLineToCalculateOutputs.signalOrder:

    # TODO: if isinstance(s, BlockOutputSignal):
    if not isinstance(s, SimulationInputSignal):
        # only implement caching for intermediate computaion results.
        # I.e. exclude the simulation input signals

        signalsToCache.append( s )

commandToCacheIntermediateResults = CommandCacheOutputs( signalsToCache )

# build the API function calcPrimaryResults() that calculates the outputs of the simulation.
# Further, it stores intermediate results
commandToPublishTheResults = PutAPIFunction("calcResults_1", 
                                            inputSignals=simulationInputSignalsForCalcOutputs,   # TODO: only add the elements that are inputs
                                            outputSignals=outputSignals, 
                                            executionCommands=[ commandToCalcTheResultsToPublish, commandToCacheIntermediateResults ] )

# Initialize the list of commands to execute to update the states
commandsToExecuteForStateUpdate = []

# restore the cache of output signals to update the states
commandsToExecuteForStateUpdate.append( CommandRestoreCache(commandToCacheIntermediateResults) )

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
    
    #
    # TODO: ensure somehow that variables are reserved for the inputs to the blocks
    #       whose states are updated
    #

    commandsToExecuteForStateUpdate.append( CommandCalculateOutputs(executionLineForCurrentOrder, dependencySignals__, defineVarsForOutputs = False) )

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
#    sUpCmd = CommandCalculateOutputs( blocksWhoseStatesToUpdate)

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

# code to reset add blocks in the simulation
commandsToExecuteForStateReset = CommandResetStates( blockList=sim.getBlocksArray() )

# create an API-function resetStates()
commandToResetStates = PutAPIFunction( nameAPI = 'resetStates', 
                                        inputSignals=[], 
                                        outputSignals=[], 
                                        executionCommands=[commandsToExecuteForStateReset] )


# define the interfacing class
commandToExecute_simulation = PutSimulation(    nameAPI = 'testSimulation',
                                                resetCommand = commandToResetStates, 
                                                updateCommand = commandToUpdateStates,
                                                outputCommand = commandToPublishTheResults
                                            )


# specify what the input signals shall be in the runtime
inputSignalsMapping = {}
inputSignalsMapping[ U ] = 1.0
inputSignalsMapping[ E1 ] = 2.0
inputSignalsMapping[ E2 ] = 3.0

commandToExecute = PutRuntimeCpp(commandToExecute_simulation, inputSignalsMapping=inputSignalsMapping)

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

sourcecode = commandToExecute.codeGen('c++', 'code')


print(Style.DIM + sourcecode)
print()

# finish
#sim.export_ortdrun('RTMain')
#sim.ShowBlocks()



f = open("generated/simulation.cpp", "w")
f.write( sourcecode )
f.close()










