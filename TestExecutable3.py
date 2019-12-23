import dynamics as dy

import os
import json

from colorama import init,  Fore, Back, Style
init(autoreset=True)

#
# python3 -m http.server
#

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

    yFb << y

    return y


def firstOrderAndGain( u : dy.Signal, z_inf, gain, name : str):

    yFb = dy.signal()

    s = dy.add( [ yFb, u ], [ -z_inf, 1 ] ).setNameOfOrigin(name + '_s (add)').setName('s'+name+'')
    d = dy.delay( s).setNameOfOrigin(name + '_d (delay)').setName('d'+name+'')
    y = dy.gain( d, gain).setNameOfOrigin(name + '_y (gain)').setName('y'+name+'')

    yFb << y

    return y


def dInt( u : dy.Signal, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, 1 ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb << y

    return y

def eInt( u : dy.Signal, Ts : float, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, Ts ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i ).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

    yFb << y

    return y

def diff( u : dy.Signal, name : str):

    i = dy.delay( u ).setNameOfOrigin(name + '_i (delay)').setName(name + '_i')
    y = dy.add( [ i, u ], [ -1, 1 ] ).setNameOfOrigin(name + '_y (add)').setName(name + '_y')

    return y

def counter():

    increase = dy.const(1, dy.DataTypeInt32(1) )

    cnt = dy.signal()
    
    cnt << dy.delay(cnt + increase)

    return cnt




testname = 'inline_subsystem' # 'test1', 'test_integrator', 'test_oscillator_controlled', 'test_oscillator_from_lib_controlled'
test_modification_1 = True  # option should not have an influence on the result
test_modification_2 = False # shall raise an error once this is true

# testname = 'test_oscillator_controlled' # TODO: this fails

if testname == 'test1':

    baseDatatype = dy.DataTypeFloat64(1) 
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

    baseDatatype = dy.DataTypeFloat64(1) 

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

    baseDatatype = dy.DataTypeFloat64(1) 

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

if testname == 'test_oscillator_with_modulation':

    baseDatatype = dy.DataTypeFloat64(1) 

    U = dy.system_input( baseDatatype ).setName('extU')
    damping = dy.system_input( baseDatatype ).setName('dampling')
    spring = dy.system_input( baseDatatype ).setName('spring')

    x = dy.signal()
    v = dy.signal()

    acc = U - damping * v - spring * x # TODO: make this work

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


    baseDatatype = dy.DataTypeFloat64(1) 

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
        controlVar = u_p + u_d + u_i  # TODO: compilation fails if u_i is removed because u_i is not connected to sth.

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

if testname == 'basic':

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    x1 = dy.delay(U)

    outputSignals = [ x1 ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0
    
if testname == 'test_oscillator_from_lib':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    outputSignals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    outputSignals[0].setName('x')
    outputSignals[1].setName('v')

    x = dy.delay( outputSignals[0] ).setName('x_delay')
    v = dy.delay( outputSignals[1] ).setName('v_delay')



    outputSignals = [ x, v ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0


if testname == 'test_oscillator_from_lib':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    outputSignals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    outputSignals[0].setName('x')
    outputSignals[1].setName('v')

    x = outputSignals[0].setName('x')
    v = outputSignals[1].setName('v')

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    outputSignals = [ x ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0


if testname == 'test_triggered_oscillator_from_lib':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    outputSignals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    outputSignals[0].setName('x')
    outputSignals[1].setName('v')

    x = outputSignals[0].setName('x')
    v = outputSignals[1].setName('v')

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    outputSignals = [ x ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0



if testname == 'test_comparison':

    baseDatatype = dy.DataTypeFloat64(1) 
    u1 = dy.system_input( baseDatatype ).setName('u1')
    u2 = dy.system_input( baseDatatype ).setName('u2')

    isGreater = dy.comparison(left = u1, right = u2, operator = '>' )

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    outputSignals = [ isGreater ]

    inputSignalsMapping = {}
    inputSignalsMapping[ u1 ] = 1.0
    inputSignalsMapping[ u2 ] = 1.1


if testname == 'test_step':
    y = dy.float64(3) * dy.step(10) + dy.float64(-5) * dy.step(40) + dy.float64(2) * dy.step(70) 

    outputSignals = [ y ]
    inputSignalsMapping = {}

if testname == 'test_ramp':
    y1 = dy.float64(3) * dy.ramp(10) - dy.float64(2) * dy.ramp(70) 
    y2 = dy.float64(-5) * dy.ramp(40)

    y1.setName('y1')

    outputSignals = [ y1, y2 ]
    inputSignalsMapping = {}



if testname == 'test_datatype_convertion':
    y = dy.int32(333)

    y = dy.convert(y, dy.DataTypeFloat64(1) )
    
    outputSignals = [ y ]
    inputSignalsMapping = {}


if testname == 'dtf_lowpass_1_order':

    u = dy.float64(1.0)

    y = dy.dtf_lowpass_1_order(u, z_infinity=0.95 )
    
    outputSignals = [ y ]
    inputSignalsMapping = {}


if testname == 'dtf_lowpass_1_order_V2':

    u = dy.float64(1.0)

    y1 = dy.dtf_lowpass_1_order(u,  z_infinity=0.97 ).setName('_1st_order')
    y2 = dy.dtf_lowpass_1_order(y1, z_infinity=0.97 ).setName('_2nd_order')
    y3 = dy.dtf_lowpass_1_order(y2, z_infinity=0.97 ).setName('_3rd_order')
    y4 = dy.dtf_lowpass_1_order(y3, z_infinity=0.97 ).setName('_4th_order')
    y5 = dy.dtf_lowpass_1_order(y4, z_infinity=0.97 ).setName('_5th_order')
    
    outputSignals = [ y1, y2, y3, y4, y5 ]
    inputSignalsMapping = {}


if testname == 'dtf_filter':

    # b = [  1, 1     ] # num
    # a = [     -0.9   ] # den


    import numpy as np
    import control as cntr

    def get_zm1_coeff(L):
        
        numcf = L.num[0][0]
        dencf = L.den[0][0]
        
        N = len(dencf)-1
        M = len(numcf)-1

        # convert to normalized z^-1 representation
        a0 = dencf[0]
        
        numcf_ = np.concatenate( [np.zeros(N-M), numcf] ) / a0
        dencf_ = dencf[1:] / a0
        
        return numcf_, dencf_



    # some transfer function calcus 
    z = cntr.TransferFunction([1,0], [1], True)

    L = (1-0.96) / (z-0.96)
    L2 = L*L

    # p-controlled system
    kp = 2

    # calc response of the closed loop
    T = kp*L2 / ( 1 + kp*L2 )

    # convert the transfer function T to the representation needed for dy.dtf_filter
    b, a = get_zm1_coeff(T)

    # system input
    u = dy.float64(1.0)

    # implement the transfer function
    y = dy.dtf_filter(u, num_coeff=b, den_coeff=a ).setName('y')
    

    outputSignals = [ y ]
    inputSignalsMapping = {}


if testname == 'switchNto1':
    switch_state = dy.system_input( dy.DataTypeInt32(1) ).setName('switch_state')

    u1 = dy.float64(1.0)
    u2 = dy.float64(2.0)
    u3 = dy.float64(3.0)
    u4 = dy.float64(4.0)

    y = dy.switchNto1( state=switch_state, inputs=[u1,u2,u3,u4] )
    
    outputSignals = [ y ]
    inputSignalsMapping = {}




if testname == 'test_triggered_subsystem':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 

    u1 = dy.system_input( baseDatatype ).setName('u1')
    u2 = dy.system_input( baseDatatype ).setName('u2')
    isGreater = dy.comparison(left = u1, right = u2, operator = '>' ).setName('isGreater')


    U = dy.system_input( baseDatatype ).setName('input')

    outputSignals = dy.triggered_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U}, trigger=isGreater )

    outputSignals[0].setName('x')
    outputSignals[1].setName('v')

    x = outputSignals[0].setName('x')
    v = outputSignals[1].setName('v')

    x = dy.delay( outputSignals[0] ).setName('x_delay')
    v = dy.delay( outputSignals[1] ).setName('v_delay')

    outputSignals = [ x, v ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0


if testname == 'test_triggered_subsystem_2':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 

    i_activate = dy.system_input( dy.DataTypeInt32(1) ).setName('i_activate')

    i = dy.counter()

#    isGreater = dy.comparison(left = i_activate, right = i, operator = '<' ).setName('isGreater')
    isGreater = i_activate < i 
    isGreater.setName('isGreater')


    U = dy.system_input( baseDatatype ).setName('input')

    outputSignals = dy.triggered_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U}, trigger=isGreater )

    outputSignals[0].setName('x')
    outputSignals[1].setName('v')

    x = outputSignals[0].setName('x')
    v = outputSignals[1].setName('v')

    x = dy.delay( outputSignals[0] ).setName('x_delay')
    v = dy.delay( outputSignals[1] ).setName('v_delay')

    outputSignals = [ x, v ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0





if testname == 'test_forloop_subsystem':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 

    i_max = dy.system_input( dy.DataTypeInt32(1) ).setName('i_max')


    U = dy.system_input( baseDatatype ).setName('input')

    outputSignals = dy.for_loop_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U}, i_max=i_max )

    outputSignals[0].setName('x')
    outputSignals[1].setName('v')

    x = outputSignals[0].setName('x')
    v = outputSignals[1].setName('v')

    x = dy.delay( outputSignals[0] ).setName('x_delay')
    v = dy.delay( outputSignals[1] ).setName('v_delay')

    outputSignals = [ x, v ]

    inputSignalsMapping = {}
    inputSignalsMapping[ U ] = 1.0


    
if testname == 'inline_subsystem':
    

    
    
#     def subsystem(U_input, damping_input):

#         dy.enter_system('oscillator')

#         print(dy.get_simulation_context())

# #         baseDatatype = dy.DataTypeFloat64(1) 

#         # input to the system
#         damping = dy.system_input( None ).setName('damping')
#         U = dy.system_input( None ).setName('u')

#         inputSignals = [damping, U]

#         # connect (proposal), also derives datatypes from the sources, if available
#         damping.connect( damping_input )
#         U.connect( U_input )

#         x = dy.signal()
#         v = dy.signal()

#         acc = dy.add( [ U, v, x ], [ 1, -0.5, -0.1 ] ).setNameOfOrigin('acceleration model')

#         v << eInt( acc, Ts=0.1, name="intV").setName('x')
#         x << eInt( v, Ts=0.1, name="intX").setName('v')

#         # define the outputs of the simulation
#         x.setName('x')
#         v.setName('v')

#         # define output variables
#         outputSignals = [ x,v ]

#         # store this system in a reference variable
#         # i.e. store connections do not compile or propagate the datatypes now
#         stored_subsystem = dy.store_current_system(inputSignals, outputSignals)


#         dy.leave_system()

#         return x,y





    class subsystem_if:
        def __init__(self, condition_signal : dy.SignalUserTemplate):
            self._condition_signal = condition_signal

            self._outputs = []

        def add_output(self, signal : dy.SignalUserTemplate):

            print("added output signal " + signal.name)
            self._outputs.append(signal)


        def __enter__(self):

            print("Entering if subsystem")

            dy.enter_subsystem('if_subsystem')

            return self


        def __exit__(self, type, value, traceback):

            print("leave if subsystem")

            # set the outputs of the system
            dy.get_simulation_context().setPrimaryOutputs( dy.unwrap_list( self._outputs ) )

            # Please note: in case it is really necessary to specify a system != None here, use the upper-level system
            # not the embedded one.

            # store an embeeder prototype (as generated by dy.GenericSubsystem) into the date structure of the subsystem
            dy.get_simulation_context().embeddedingBlockPrototype = dy.GenericSubsystem( sim=dy.get_simulation_context().UpperLevelSim, inputSignals=None, manifest=None, additionalInputs=None )


            # TODO: add a system wrapper/embedded (e.g. this if-block) to leave_system
            dy.leave_system()


            #
            



            # 1) find the outputs (they shall be defined)   ---> self._outputs
            # 2) get the inputs as a result of an intersection between two simulations
            #
            #       -> During the compile process, the borders to the upper-level simulation shall be detected
            #
            #       -> split the compilation process into two phases: propagate datatypes, and generate code
            #
            #
            #  -- below is obsolete --
            #
            # 3) cut the inputs and replace them by dy.system_input
            # 4) store the subsystem: stored_subsystem = dy.store_current_system(inputSignals, outputSignals)
            # 5) build an new block for embedding the subsystem. The variable stored_subsystem is a parameter
            # 6) connect the inputs of the block to the cutted signals
            #
            # 7) Datatype propagation: ???
            #
            # 8) on compile of the surrounding system, the embedding block will compile the nested subsystem



    baseDatatype = dy.DataTypeFloat64(1) 

    switch = dy.system_input( baseDatatype ).setName('switch')
    inpu = dy.system_input( baseDatatype ).setName('input')

    # outputSignals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    # outputSignals[0].setName('x')
    # outputSignals[1].setName('v')


    with subsystem_if( switch > dy.float64(1.0) ) as system:

        # the signal 'inpu' is automatically detected to be an input to the subsystem

        tmp = dy.float64(2.5).setName('tmp')

        # warum ist output dem system 'simulation' zugeordnet und nicht zu 'if_subsystem'?
        # vor compilierung gehört es zu 'if_subsystem' 
        output = inpu * tmp 


        test = dy.delay( tmp )
        test2 = dy.delay( inpu )

        output.setName('output_of_if')
        system.add_output(output)
        

    # main simulation ouput
    outputSignals = [ output ]

    inputSignalsMapping = {}






# set the outputs of the system
dy.set_primary_outputs(outputSignals)

# Compile system (propagate datatypes)
compileResults = dy.compile_current_system()


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


