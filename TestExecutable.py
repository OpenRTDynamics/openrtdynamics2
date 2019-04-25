

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


c1 = dyn_const(sim, 1.123).setNameOfOrigin('c1 - const').setName('c1')

c2 = dyn_const(sim, 10).setNameOfOrigin('c1 - const').setName('c2')

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
c3 = dyn_const(sim, 1.123).setNameOfOrigin('c3 - const').setName('c3')
udel2__ = dyn_gain(sim, udel2_, 3).setNameOfOrigin('gain').setName('udel2__')

resultSecond = dyn_add(sim, [c3, udel2__], [1,-1]).setNameOfOrigin('resultSecond').setName('resultSecond')



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

print()
print("-------- Find dependencies for calcularing 'result'  --------")
print()

E=BuildExecutionPath()
executionLine1 = E.getExecutionLine( result )
executionLine1.printExecutionLine()

print()
print("-------- Find dependencies for calcularing 'resultSecond'  --------")
print()

E=BuildExecutionPath()
executionLine2 = E.getExecutionLine( resultSecond )
executionLine2.printExecutionLine()

print()
print("-------- concatenate execution lines  --------")
print()

executionLine1.appendExecutionLine( executionLine2 )
executionLine1.printExecutionLine()

# finish
#sim.export_ortdrun('RTMain')
#sim.ShowBlocks()


















