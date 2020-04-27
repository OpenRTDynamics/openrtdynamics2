import openrtdynamics2.lang as dy

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
system = dy.enter_system('simulation')

# list to collect systems imported from libraries
library_entries = []



def firstOrder( u : dy.Signal, z_inf, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ -z_inf, 1 ] ).setName(name + '_i')
    y = dy.delay( i).setName(name + '_y')

    yFb << y

    return y


def firstOrderAndGain( u : dy.Signal, z_inf, gain, name : str):

    yFb = dy.signal()

    s = dy.add( [ yFb, u ], [ -z_inf, 1 ] ).setName('s'+name+'')
    d = dy.delay( s).setName('d'+name+'')
    y = dy.gain( d, gain).setName('y'+name+'')

    yFb << y

    return y


def dInt( u : dy.Signal, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, 1 ] ).setName(name + '_i')
    y = dy.delay( i).setName(name + '_y')

    yFb << y

    return y

def eInt( u : dy.Signal, Ts : float, name : str, initial_state = None):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, Ts ] ).setName(name + '_i')
    y = dy.delay( i, initial_state ).setName(name + '_y')

    yFb << y

    return y

def diff( u : dy.Signal, name : str):

    i = dy.delay( u ).setName(name + '_i')
    y = dy.add( [ i, u ], [ -1, 1 ] ).setName(name + '_y')

    return y




testname = 'system_state_machine2' # 
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
    output_signals = [ y, y2 ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0
    input_signals_mapping[ E1 ] = 2.0
    input_signals_mapping[ E2 ] = 3.0



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
    output_signals = [  y6 ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0

if testname == 'test_oscillator':

    baseDatatype = dy.DataTypeFloat64(1) 

    U = dy.system_input( baseDatatype ).setName('extU')

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

    v << eInt( acc, Ts=0.1, name="intV")
    x << eInt( v, Ts=0.1, name="intX")

    # define the outputs of the simulation
    output_signals = [ x, v ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0

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
    output_signals = [ x, v ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0

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
    output_signals = [ x,v ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ reference ] = 1.0
    input_signals_mapping[ Kp ] = 0.3
    input_signals_mapping[ Kd ] = 0.3
    input_signals_mapping[ Ki ] = 0.3

if testname == 'basic':

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    x1 = dy.delay(U)

    output_signals = [ x1 ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0
    
if testname == 'test_oscillator_from_lib':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    output_signals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    output_signals[0].setName('x')
    output_signals[1].setName('v')

    x = dy.delay( output_signals[0] ).setName('x_delay')
    v = dy.delay( output_signals[1] ).setName('v_delay')



    output_signals = [ x, v ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0


if testname == 'test_oscillator_from_lib':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    output_signals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    output_signals[0].setName('x')
    output_signals[1].setName('v')

    x = output_signals[0].setName('x')
    v = output_signals[1].setName('v')

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    output_signals = [ x ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0


if testname == 'test_triggered_oscillator_from_lib':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).setName('input')

    output_signals = dy.generic_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U} )

    output_signals[0].setName('x')
    output_signals[1].setName('v')

    x = output_signals[0].setName('x')
    v = output_signals[1].setName('v')

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    output_signals = [ x ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0



if testname == 'test_comparison':

    baseDatatype = dy.DataTypeFloat64(1) 
    u1 = dy.system_input( baseDatatype ).setName('u1')
    u2 = dy.system_input( baseDatatype ).setName('u2')

    isGreater = dy.comparison(left = u1, right = u2, operator = '>' )

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    output_signals = [ isGreater ]

    input_signals_mapping = {}
    input_signals_mapping[ u1 ] = 1.0
    input_signals_mapping[ u2 ] = 1.1


if testname == 'test_step':
    y = dy.float64(3) * dy.step(10) + dy.float64(-5) * dy.step(40) + dy.float64(2) * dy.step(70) 

    output_signals = [ y ]
    input_signals_mapping = {}

if testname == 'test_ramp':
    y1 = dy.float64(3) * dy.ramp(10) - dy.float64(2) * dy.ramp(70) 
    y2 = dy.float64(-5) * dy.ramp(40)

    y1.setName('y1')

    output_signals = [ y1, y2 ]
    input_signals_mapping = {}



if testname == 'test_datatype_convertion':
    y = dy.int32(333)

    y = dy.convert(y, dy.DataTypeFloat64(1) )
    
    output_signals = [ y ]
    input_signals_mapping = {}


if testname == 'dtf_lowpass_1_order':

    u = dy.float64(1.0)

    y = dy.dtf_lowpass_1_order(u, z_infinity=0.95 )
    
    output_signals = [ y ]
    input_signals_mapping = {}


if testname == 'dtf_lowpass_1_order_V2':

    u = dy.float64(1.0)

    y1 = dy.dtf_lowpass_1_order(u,  z_infinity=0.97 ).setName('_1st_order')
    y2 = dy.dtf_lowpass_1_order(y1, z_infinity=0.97 ).setName('_2nd_order')
    y3 = dy.dtf_lowpass_1_order(y2, z_infinity=0.97 ).setName('_3rd_order')
    y4 = dy.dtf_lowpass_1_order(y3, z_infinity=0.97 ).setName('_4th_order')
    y5 = dy.dtf_lowpass_1_order(y4, z_infinity=0.97 ).setName('_5th_order')
    
    output_signals = [ y1, y2, y3, y4, y5 ]
    input_signals_mapping = {}


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
    

    output_signals = [ y ]
    input_signals_mapping = {}


if testname == 'switchNto1':
    switch_state = dy.system_input( dy.DataTypeInt32(1) ).setName('switch_state')

    u1 = dy.float64(1.0)
    u2 = dy.float64(2.0)
    u3 = dy.float64(3.0)
    u4 = dy.float64(4.0)

    y = dy.switchNto1( state=switch_state, inputs=[u1,u2,u3,u4] )
    
    output_signals = [ y ]
    input_signals_mapping = {}




if testname == 'test_triggered_subsystem':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 

    u1 = dy.system_input( baseDatatype ).setName('u1')
    u2 = dy.system_input( baseDatatype ).setName('u2')
    isGreater = dy.comparison(left = u1, right = u2, operator = '>' ).setName('isGreater')


    U = dy.system_input( baseDatatype ).setName('input')

    output_signals = dy.triggered_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U}, trigger=isGreater )

    output_signals[0].setName('x')
    output_signals[1].setName('v')

    x = output_signals[0].setName('x')
    v = output_signals[1].setName('v')

    x = dy.delay( output_signals[0] ).setName('x_delay')
    v = dy.delay( output_signals[1] ).setName('v_delay')

    output_signals = [ x, v ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0


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

    output_signals = dy.triggered_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U}, trigger=isGreater )

    output_signals[0].setName('x')
    output_signals[1].setName('v')

    x = output_signals[0].setName('x')
    v = output_signals[1].setName('v')

    x = dy.delay( output_signals[0] ).setName('x_delay')
    v = dy.delay( output_signals[1] ).setName('v_delay')

    output_signals = [ x, v ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0





if testname == 'test_forloop_subsystem':
    import TestLibray as TestLibray
    libraryEntries.append( TestLibray.oscillator )

    baseDatatype = dy.DataTypeFloat64(1) 

    i_max = dy.system_input( dy.DataTypeInt32(1) ).setName('i_max')


    U = dy.system_input( baseDatatype ).setName('input')

    output_signals = dy.for_loop_subsystem( manifest=TestLibray.oscillator.manifest, inputSignals={'u' : U}, i_max=i_max )

    output_signals[0].setName('x')
    output_signals[1].setName('v')

    x = output_signals[0].setName('x')
    v = output_signals[1].setName('v')

    x = dy.delay( output_signals[0] ).setName('x_delay')
    v = dy.delay( output_signals[1] ).setName('v_delay')

    output_signals = [ x, v ]

    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0


    
if testname == 'inline_subsystem':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    switch = dy.system_input( baseDatatype ).setName('switch')
    input = dy.system_input( baseDatatype ).setName('input')


#    with dy.sub_if( switch > dy.float64(1.0) ) as system:
    with dy.sub() as system:

        # the signal 'input' is automatically detected to be an input to the subsystem

        tmp = dy.float64(2.5).setName('const25')


        output = input * tmp 


        # test = dy.delay( tmp )
        # test2 = dy.delay( input )

        output.setName('output_of_if')
        output = system.add_output(output)

        output.setName("embedder_output")


    # optional y = output
    y = dy.float64(10.0) * output


    # main simulation ouput
#    output_signals = [ output ]
    output_signals = [ y ]

    input_signals_mapping = {}




if testname == 'inline_ifsubsystem':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    switch = dy.system_input( baseDatatype ).setName('switch_condition')   # if this was named 'switch' c++ fails beucause it is a reserved keyword there
    input = dy.system_input( baseDatatype ).setName('input')


    ramp = dy.ramp(10).setName('ramp')

    activated = ramp > switch


    with dy.sub_if( activated ) as system:

        # the signal 'input' is automatically detected to be an input to the subsystem

        tmp = dy.float64(2.5).setName('const25')
        output = input * tmp 

        output.setName('output_of_if')
        
        output = system.add_output(output)

        output.setName("embedder_output")


    # optional y = output
    y = dy.float64(10.0) * output

    # main simulation ouput
    output_signals = [ y, ramp ]

    input_signals_mapping = {}








if testname == 'inline_ifsubsystem_oscillator':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    activation_sample = dy.system_input( baseDatatype ).setName('activation_sample')
    U = dy.system_input( baseDatatype ).setName('osc_excitement')

    with dy.sub_if( (dy.ramp(0) > activation_sample) * (dy.ramp(100) < activation_sample), prevent_output_computation=False ) as system:

        x = dy.signal()
        v = dy.signal()

        acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

        v << eInt( acc, Ts=0.1, name="intV", initial_state=-1.0 )
        x << eInt( v, Ts=0.1, name="intX")

        output_x = system.add_output(x)
        output_v = system.add_output(v)

    # main simulation ouput
    output_signals = [ output_x, output_v ]

    input_signals_mapping = {}






if testname == 'system_switch':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    active_system = dy.system_input( dy.DataTypeInt32(1) ).setName('active_system')
    U = dy.system_input( baseDatatype ).setName('osc_excitement')

    with dy.sub_switch( "switch1", active_system ) as switch:

        with switch.new_subsystem('default_system') as system: # NOTE: do not put c++ keywords as system names
            # this is defined to be the default subsystem
            # the datatypes of the outputs defined here a
            # used for the main outputs of the function 
            # dy.sub_switch

            # inputs are [] (no inputs)

            x = dy.float64(0.0).setName('x_def')
            v = dy.float64(0.0).setName('v_def')

            system.set_switched_outputs([ x, v ])
                    

        with switch.new_subsystem('running_system') as system:
            # inputs are [U]

            x = dy.signal()
            v = dy.signal()

            acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

            v << eInt( acc, Ts=0.1, name="intV", initial_state=-1.0 )
            x << eInt( v,   Ts=0.1, name="intX" )

            system.set_switched_outputs([ x, v ])


            #  python3 -m http.server

    output_x = switch.outputs[0].setName("ox")
    output_v = switch.outputs[1].setName("ov")

    # main simulation ouput
    output_signals = [ output_x, output_v ]

    input_signals_mapping = {}







if testname == 'system_state_machine':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    U2 = dy.system_input( baseDatatype ).setName('osc_excitement')

    U = U2 * dy.float64(1.234)
    U.setName("stachmachine_input_U")

    with dy.sub_statemachine( "statemachine1" ) as switch:


        with switch.new_subsystem('state_A') as system: # NOTE: do not put c++ keywords as system names

            x = dy.float64(0.0).setName('x_def')
            v = dy.float64(0.0).setName('v_def')


            counter = dy.counter().setName('counter')
            timeout = ( counter > dy.int32(10) ).setName('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=1 ).setName('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)


        with switch.new_subsystem('state_B') as system:

            x = dy.signal()
            v = dy.signal()

            acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

            v << eInt( acc, Ts=0.1, name="intV", initial_state=-1.0 )
            x << eInt( v,   Ts=0.1, name="intX" )

            counter = dy.counter().setName('counter')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=counter > dy.int32(50), new_value=0 ).setName('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)



    output_x = switch.outputs[0].setName("ox")
    output_v = switch.outputs[1].setName("ov")
    counter = switch.outputs[2].setName("counter")

    state = switch.state.setName('state_control')

    # main simulation ouput
    output_signals = [ output_x, output_v, state, counter ]

    input_signals_mapping = {}







if testname == 'system_state_machine2':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    number_of_samples_to_stay_in_A = dy.system_input( baseDatatype ).setName('number_of_samples_to_stay_in_A')
    threshold_for_x_to_leave_B = dy.system_input( baseDatatype ).setName('threshold_for_x_to_leave_B')


    U2 = dy.system_input( baseDatatype ).setName('osc_excitement')

    U = U2 * dy.float64(1.234)
    U.setName("stachmachine_input_U")

    with dy.sub_statemachine( "statemachine1" ) as switch:


        with switch.new_subsystem('state_A') as system: # NOTE: do not put c++ keywords as system names

            x = dy.float64(0.0).setName('x_def')
            v = dy.float64(0.0).setName('v_def')


            counter = dy.counter().setName('counter')
            timeout = ( counter > number_of_samples_to_stay_in_A ).setName('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=1 ).setName('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)


        with switch.new_subsystem('state_B') as system:

            x = dy.signal()
            v = dy.signal()

            acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).setNameOfOrigin('acc').setName('acc')

            v << eInt( acc, Ts=0.1, name="intV", initial_state=-1.0 )
            x << eInt( v,   Ts=0.1, name="intX" )

            counter = dy.counter().setName('counter')
            leave_this_state = (x > threshold_for_x_to_leave_B).setName("leave_this_state")
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=leave_this_state, new_value=0 ).setName('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)



    output_x = switch.outputs[0].setName("ox")
    output_v = switch.outputs[1].setName("ov")
    counter = switch.outputs[2].setName("counter")

    state = switch.state.setName('state_control')

    # main simulation ouput
    output_signals = [ output_x, output_v, state, counter ]

    input_signals_mapping = {}


#
#
# general
#
#




# set the outputs of the system
dy.set_primary_outputs(output_signals)

# Compile system (propagate datatypes)
compile_results = dy.compile_current_system()


#
# Build an executable based on a template
#

runtime_template = dy.WasmRuntimeCpp(compile_results, input_signals_mapping=input_signals_mapping)

#runtime_template = dy.PutBasicRuntimeCpp(compileResults, input_signals_mapping=input_signals_mapping)



# add (pre-compiled) systems from the libraries
runtime_template.include_systems( library_entries )

#
# list all execution lists
#

dy.show_execution_lines(compile_results)

#
# generate c++ cpde
#

print()
print(Style.BRIGHT + "-------- Code generation  --------")
print()

sourcecode, manifest = runtime_template.code_gen()

print(Style.DIM + sourcecode)

print()
print(Style.BRIGHT + "-------- Manifest  --------")
print()
print(json.dumps(manifest, indent=4, sort_keys=True))


# write generated code into a folder and build
runtime_template.write_code("generated/")
runtime_template.build()

# run the code (in case the runtime template supports it)
results = runtime_template.run()


