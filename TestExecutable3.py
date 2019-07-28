import dynamics as dy

import os
import json

from colorama import init,  Fore, Back, Style
init(autoreset=True)




#
# Enter a new system (simulation)
#
sim = dy.enter_system('simulation')

# list to collect systems importd from libraries
libraryEntries = []



def firstOrder( u : dy.Signal, z_inf, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb.setequal( y )

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


testname = 'test_oscillator' # 'test1', 'test_integrator', 'test_oscillator_controlled', 'test_oscillator_from_lib_controlled'
test_modification_1 = True  # option should not have an influence on the result
test_modification_2 = False # shall raise an error once this is true

if testname == 'test1':

    baseDatatype = dy.DataTypeFloat(1) 
    # baseDatatype = DataTypeInt32(1) 

    U = dy.system_input( baseDatatype ).setName('extU')

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

    U = dy.system_input( baseDatatype ).setName('extU')

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

    v << eInt( acc, Ts=0.1, name="intV")
    x << eInt( v, Ts=0.1, name="intX")

    # define the outputs of the simulation
    outputSignals = [ x, v ]

    # specify what the input signals shall be in the runtime
    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0


if testname == 'test_oscillator_controlled':

    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )


    baseDatatype = dy.DataTypeFloat(1) 

    # input to simulations
    # Kp = SimulationInputSignal(sim, port=0, datatype=baseDatatype ).setName('extU')

    Kp = dy.system_input( baseDatatype ).setName('Kp')
    Kd = dy.system_input( baseDatatype ).setName('Kd')
    Ki = dy.system_input( baseDatatype ).setName('Ki')
    reference = dy.system_input( baseDatatype ).setName('ref')

    #
    # reference = dy.const( 2.5, baseDatatype )

    # 
    controlledVariableFb = dy.signal()

    # control error
    controlError = dy.add( [ reference, controlledVariableFb ], [ 1, -1 ] ).setName('err')

    # P
    u_p = dy.operator1( [ Kp, controlError ], '*' ).setName('u_p')

    # D
    d = diff( controlError, 'PID_D')
    u_d = dy.operator1( [ Kd, d ], '*' ).setName('u_d')

    # I
    u_i_tmp = dy.signal()
    u_i = dy.delay(controlError + u_i_tmp) * Ki

    u_i_tmp << u_i

    u_i_tmp.setName('u_i')

    if test_modification_1:
        u_i = u_i_tmp

    # sum up
    if not test_modification_2:
        controlVar = u_p + u_d + u_i  # TODO: compilation fails if u_i is removed

    else:
        # shall raise an error
        anonymous_signal = dy.signal()
        controlVar = u_p + u_d + u_i + anonymous_signal

    controlVar.setName('u')

    # stupid test
    fancyVariable = controlVar - dy.const( 2.5, baseDatatype ) / dy.const( 1.5, baseDatatype )

    # plant starts here
    U = controlVar

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -1.1, -0.1 ] ).setNameOfOrigin('acceleration model')

    v << eInt( acc, Ts=0.1, name="intV").setName('x')
    x << eInt( v, Ts=0.1, name="intX").setName('v')

    # x is the controlled variable
    controlledVariableFb << x
    
    # define the outputs of the simulation
    x.setName('x')
    v.setName('v')
    outputSignals = [ x,v ]

    # specify what the input signals shall be in the runtime
    inputSignalsMapping = {}
    inputSignalsMapping[ reference ] = 1.0
    inputSignalsMapping[ Kp ] = 0.3
    inputSignalsMapping[ Kd ] = 0.3
    inputSignalsMapping[ Ki ] = 0.3

if testname == 'test_oscillator_from_lib_controlled':
    # import TestLibray as TestLibray
    # libraryEntries.append( TestLibray.oscillator )


    baseDatatype = dy.DataTypeFloat(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    x1 = dy.delay(U) # * dy.const( 2.5, baseDatatype )

    outputSignals = [ x1 ]


    # TestLibray.oscillator



# Compile system (propagate datatypes)
compileResults = dy.compile_current_system(outputSignals)


#
# Build an executable based on a template
#

runtimeCodeTemplate = dy.WasmRuntimeCpp(compileResults, inputSignalsMapping=inputSignalsMapping)

# add (pre-compiled) systems from the libraries
runtimeCodeTemplate.include_systems( libraryEntries )

#
# list all execution lists
#

print()
print(Style.BRIGHT + "-------- List all execution commands  --------")
print()

compileResults.commandToExecute.printExecution()

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


# write generated code into a folder and build
runtimeCodeTemplate.writeCode("generated/")
runtimeCodeTemplate.build()

# run the code (in case the runtime template supports it)
results = runtimeCodeTemplate.run()


