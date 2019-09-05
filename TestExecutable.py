

from libdyn import *
from irpar import *
from BlockPrototypes import *
from TraverseGraph import *
from Signal import *


@contextmanager
def ld_subsim(sim):
    print("create triggered subsimulation" )

    nestedsim = Simulation(sim, 'IFsub')

    yield nestedsim

    nestedsim.FinishSimulation()

    inlist = nestedsim.GetInputInterface()

    print("--- The following inputs go to the nested simulation ---")

    for i in inlist:

        print(  i  )

    # create new block with the inputs in inlist

    # -- Just store which type of subsimulation block to create:
    #
    # if / for / ...
    #
    # and then do later during export of the schematic
    #
    # In general, think about something to store an abstract representation of each block
    # and do all the work of parameter creation on export
    #
    # Maybe use classes for each block, instead of functions (def:)
    # class functions could be __init__ (collect parameters), check IO, export()
    #
    #
    # (This way, different backends can be supported)
    #



    print("finish triggered subsimulation")



# @contextmanager
# def ld_IF(sim, ConditionSignal):
#     print("create triggered subsimulation" )

#     nestedsim = Simulation(sim, 'IFsub')

#     yield nestedsim

#     print("finish triggered subsimulation")



# new simulation
sim = Simulation(None, 'main')


c1 = dyn_const(sim, 1.123, DataTypeFloat64(1) ).setNameOfOrigin('c1 - const').setName('c1')

c2 = dyn_const(sim, 10, DataTypeFloat64(1) ).setNameOfOrigin('c1 - const').setName('c2')

print()
print('origin of c1')
c1.ShowOrigin()
print()

u = dyn_add(sim, [c1, c2], [1,-1]).setNameOfOrigin('add c1 - c2').setName('u')



# open feedback loop
u2_feedback = Signal(sim)
u2_feedback.setName('u2_feedback')

u2 = dyn_add(sim, [u, u2_feedback], [1,1]).setNameOfOrigin('add u + u2').setName('u2')

u2_delayed1 = dyn_delay(sim, u2 ).setNameOfOrigin('delay u2 A').setName('u2_delayed1')
u2_delayed2 = dyn_delay(sim, u2 ).setNameOfOrigin('delay u2 B').setName('u2_delayed2')



u2_feedback.setequal( u2_delayed1 )


udel2_ = dyn_gain(sim, u2_delayed2, 2).setNameOfOrigin('gain').setName('udel2_')

# The result signals
result = dyn_add(sim, [u2_delayed1, udel2_], [1,-1]).setNameOfOrigin('result').setName('result')


# Another result signals
c3 = dyn_const(sim, 1.123, DataTypeFloat64(1) ).setNameOfOrigin('c3 - const').setName('c3')

udel2__ = dyn_gain(sim, udel2_, 3).setNameOfOrigin('gain').setName('udel2__')

resultSecond = dyn_add(sim, [c3, udel2__], [1,-1]).setNameOfOrigin('resultSecond').setName('resultSecond')

# intentionally build an algebraic loop
AlgLoop_A = Signal(sim).setName("AlgLoop_A")
AlgLoop_B = dyn_gain(sim, AlgLoop_A, 3).setNameOfOrigin('gain_AlgLoop_B').setName('AlgLoop_B')
AlgLoop_C = dyn_add(sim, [AlgLoop_B, AlgLoop_A], [1,-1]).setNameOfOrigin('AlgLoop_C').setName('AlgLoop_C')
AlgLoop_A.setequal(AlgLoop_C)




#dyn_printf(sim, u, "sum value is")






# with ld_IF(sim, condition) as sim:
#     #pass
#     print("define simulation triggered by if")





# test 
sim.ShowBlocks()


print()
print("-------- Traverse --------")
print()
 # sim.getBlocksArray()
T = TraverseGraph()
T.forwardTraverse( c1.getSourceBlock() )



print()
print("-------- Compile connections --------")
print()
sim.CompileConnections()

print()
print("-------- print datatypes --------")
print()


sim.ShowBlocks()

#
# create execution path builder
#
E=BuildExecutionPath()


print()
print("-------- Find dependencies for calcularing 'result'  --------")
print()

executionLine1 = E.getExecutionLine( result )
executionLine1.printExecutionLine()

print()
print("-------- Find dependencies for calcularing 'resultSecond'  --------")
print()

executionLine2 = E.getExecutionLine( resultSecond )
executionLine2.printExecutionLine()

print()
print("-------- concatenate execution lines  --------")
print()

executionLine1.appendExecutionLine( executionLine2 )
executionLine1.printExecutionLine()



print()
print("-------- Build all execution paths  --------")
print()

# look into executionLine1.dependencySignals and use E.getExecutionLine( ) for each
# element. Also collect the newly appearing dependency signals in a list and also 
# call E.getExecutionLine( ) on them. Stop until no further dependend signal appear.
# finally concatenare the execution lines

# 

# start with following signals to be computed
#dependencySignals = [ result, resultSecond ]
dependencySignals = executionLine1.dependencySignals

# counter for the order (i.e. step through all delays present in the system)
order = 0

# execution line per order
executionLinePerOrder = []

while True:

    print("--------- Comuting order "+ str(order) + " --------")
    print("dependent sources:")
        
    for s in dependencySignals:
        print("  - " + s.toStr() )


    # do for each dependency Signal in the list
    nextOrderDependencySingals = []

    # collect all executions lines build in this order
    executionLinesForCurrentOrder = []



    # backwards jump over the blocks that compute dependencySignals through their states
    # result is dependencySignals__ which are the inputs to these blocks
    print("These sources are translated to (through their blocks via state-update):")

    dependencySignals__ = []
    for s in dependencySignals:

        # find out which signals are needed to calculate the states needed to calculate dependencySignals
        # returnInutsToUpdateStates

        for s_ in s.getSourceBlock().getBlockPrototype().returnInutsToUpdateStates( s ):

            print("  - " + s_.toStr() )

            # only append of this signals is not already computable
            if E.isSignalAlreadyComputable(s_):
                dependencySignals__.append(s_)

            else:
                print("    This signal is already computable (no futher execution line is calculated to this signal)")



    
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
    executionLinePerOrder.append( executionLineForCurrentOrder )

    # get the dependendy singals of the current order
    dependencySignals = executionLineForCurrentOrder.dependencySignals



    # iterate
    order = order + 1
    if len(dependencySignals) == 0:
        break

    if order == 30:
        break



#
# List all execution lists
#

print()
print("-------- List all execution paths  --------")
print()

for el in list(reversed(executionLinePerOrder)):

    el.printExecutionLine()


    pass




if False:
    print()
    print("-------- Find dependencies for calcularing 'executionLineAlgLoop_C' (an algeraic loop is intentionally present)  --------")
    print()

    # This must trigger an algebraic loop exception
    try:
        executionLineAlgLoop_C = E.getExecutionLine( AlgLoop_C )
        executionLineAlgLoop_C.printExecutionLine()
    except:
        print("Unittest for check for algeraic loop passed")





# finish
#sim.export_ortdrun('RTMain')
#sim.ShowBlocks()











