import dynamics as dy

import os
import json

from colorama import init,  Fore, Back, Style
init(autoreset=True)


#
# Enter a new system (simulation)
#
sim = dy.enter_system('main')

# example
# u = dy.const(123, datatype=dy.DataTypeFloat(1) )




def firstOrder( u : dy.Signal, z_inf, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb.setequal( y )

    # inherit datatype
    #i.setDatatype( u.getDatatype() )
    #s.deriveDatatypeFrom(u)

    return y


def firstOrderAndGain( u : dy.Signal, z_inf, gain, name : str):

    yFb = dy.signal()

    s = dy.add( [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_s (add)').setName('s'+name+'')
    d = dy.delay( s).setNameOfOrigin(name + '_d (delay)').setName('d'+name+'')
    y = dy.gain( d, gain).setNameOfOrigin(name + '_y (gain)').setName('y'+name+'')

    yFb.setequal( y )

    return y


def dInt( u : dy.Signal, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, 1 ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb.setequal( y )

    return y

def eInt( u : dy.Signal, Ts : float, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, Ts ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i ).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb.setequal( y )

    return y

def diff( u : dy.Signal, name : str):

    i = dy.delay( u ).setNameOfOrigin(name + '_i (delay)').setName(name + '_i')
    y = dy.add( [ i, u ], [ -1, 1 ] ).setNameOfOrigin(name + '_y (add)').setName(name + '_y')

    return y


testname = 'test_oscillator_controlled' # 'test1', 'test_integrator', 'test_oscillator_controlled'

if testname == 'test1':

    baseDatatype = dy.DataTypeFloat(1) 
    # baseDatatype = DataTypeInt32(1) 


    #U = dyn_const(sim, 1.123, baseDatatype ).setNameOfOrigin('U (const)').setName('U')
    U = dy.system_input( baseDatatype ).setName('extU')

    # y = firstOrder(sim, U, 0.2, name="1")
    # y = firstOrder(sim, y, 0.2, name="2")
    # y = firstOrder(sim, y, 0.2, name="3")

    y1 = firstOrderAndGain( U, 0.2, gain=0.8, name="1")
    y2 = firstOrderAndGain( y1, 0.2, gain=0.8, name="2")
    y3 = firstOrderAndGain( y2, 0.2, gain=0.8, name="3")


    E1 = dy.system_input( baseDatatype ).setName('extE1')
    E2 = dy.system_input( baseDatatype ).setName('extE2')

    y = dy.add( [ y3, E1, E2 ], [ 0.1, 0.2, 0.3] ).setNameOfOrigin('y (add)').setName('y')

    # define the outputs of the simulation
    outputSignals = [ y, y2 ]

    # specify what the input signals shall be in the runtime
    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0
    inputSignalsMapping[ E1 ] = 2.0
    inputSignalsMapping[ E2 ] = 3.0



if testname == 'test_integrator':

    baseDatatype = dy.DataTypeFloat(1) 
    # baseDatatype = DataTypeInt32(1) 


    #U = dyn_const(sim, 1.123, baseDatatype ).setNameOfOrigin('U (const)').setName('U')
    U = dy.system_input( baseDatatype ).setName('extU')


    y1 = dInt( U,  name="int1")
    y2 = dInt( y1, name="int2")
    y3 = dInt( y2, name="int3")
    y4 = dInt( y3, name="int4")
    y5 = dInt( y4, name="int5")
    y6 = dInt( y5, name="int6")


    # define the outputs of the simulation
    outputSignals = [  y6 ]

    # specify what the input signals shall be in the runtime
    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0
    


if testname == 'test_oscillator':

    baseDatatype = dy.DataTypeFloat(1) 
    # baseDatatype = DataTypeInt32(1) 


    #U = dyn_const(sim, 1.123, baseDatatype ).setNameOfOrigin('U (const)').setName('U')
    U = dy.system_input( baseDatatype ).setName('extU')

    xFb = dy.signal()
    vFb = dy.signal()

    acc = dy.add( [ U, vFb, xFb ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

    v = eInt( acc, Ts=0.1, name="intV")
    x = eInt( v, Ts=0.1, name="intX")

    xFb.setequal(x)
    vFb.setequal(v)
    

    # define the outputs of the simulation
    outputSignals = [  x,v ]

    # specify what the input signals shall be in the runtime
    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0


if testname == 'test_oscillator_controlled':

    baseDatatype = dy.DataTypeFloat(1) 

    # input to simulations
    # Kp = SimulationInputSignal(sim, port=0, datatype=baseDatatype ).setName('extU')

    Kp = dy.system_input( baseDatatype ).setName('Kp')
    Kd = dy.system_input( baseDatatype ).setName('Kd')
    reference = dy.system_input( baseDatatype ).setName('ref')

    #
    # reference = dyn_const(sim, 2.5, baseDatatype )

    # 
    controlledVariableFb = dy.Signal(sim)

    # control error
    controlError = dy.add( [ reference, controlledVariableFb ], [ 1, -1 ] ).setName('err')

    # P
    u_p = dy.operator1( [ Kp, controlError ], '*' ).setName('u_p')

    # D
    d = diff( controlError, 'PID_D')
    u_d = dy.operator1( [ Kd, d ], '*' ).setName('u_d')

    # sum up
    controlVar = dy.add( [ u_p, u_d ], [ 1, 1 ] ).setName('u')
    


    # plant starts here
    U = dy.gain( controlVar, 1.0)
    U = dy.sin( U)
    # U = controlVar

    xFb = dy.signal()
    vFb = dy.signal()

    acc = dy.add( [ U, vFb, xFb ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acceleration model')

    v = eInt( acc, Ts=0.1, name="intV")
    x = eInt( v, Ts=0.1, name="intX")

    xFb.setequal(x)
    vFb.setequal(v)
    
    #
    controlledVariableFb.setequal(x)

    # define the outputs of the simulation
    x.setName('x')
    v.setName('v')
    outputSignals = [  x,v ]

    # specify what the input signals shall be in the runtime
    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0






dy.get_simulation_context().ShowBlocks()


print()
print(Style.BRIGHT + "-------- Compile connections (determine datatypes) --------")
print()
dy.get_simulation_context().CompileConnections()

print()
print(Style.BRIGHT + "-------- print datatypes --------")
print()

dy.get_simulation_context().ShowBlocks()

print()
print(Style.BRIGHT + "-------- export graph --------")
print()

graph = dy.get_simulation_context().exportGraph()

with open( os.path.join(  'generated/graph.json' ), 'w') as outfile:  
    json.dump(graph, outfile)

#
# compile the diagram: turn the blocks and signals into a tree-structure of commands to execute
# at runtime.
#

compiler = dy.CompileDiagram()
commandToExecute = compiler.compile( dy.get_simulation_context(), outputSignals )


#
# Build an executable based on a template
#



# runtimeCodeTemplate = PutBasicRuntimeCpp(commandToExecute, inputSignalsMapping=inputSignalsMapping)

runtimeCodeTemplate = dy.WasmRuntimeCpp(commandToExecute, inputSignalsMapping=inputSignalsMapping)


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

sourcecode, manifest = runtimeCodeTemplate.codeGen(iMax = 500)

print(Style.DIM + sourcecode)

print()
print(Style.BRIGHT + "-------- Manifest  --------")
print()
print(json.dumps(manifest, indent=4, sort_keys=True))


#
runtimeCodeTemplate.writeCode("generated/")
runtimeCodeTemplate.build()

results = runtimeCodeTemplate.run()

