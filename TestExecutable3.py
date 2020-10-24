import math

import openrtdynamics2.lang as dy

import os
import json
import numpy as np

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



def firstOrder( u : dy.Signal, z_inf, name : str = ''):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ z_inf, 1 ] ).set_name(name + '_i')
    y = dy.delay( i).set_name(name + '_y')

    yFb << y

    return y


def firstOrderAndGain( u : dy.Signal, z_inf, gain, name : str = ''):

    dFb = dy.signal()

    s = dy.add( [ dFb, u ], [ z_inf, 1 ] ).set_name('s'+name+'')
    d = dy.delay( s).set_name('d'+name+'')

    dFb << d

    y = dy.gain( d, gain).set_name('y'+name+'')

    return y


def dInt( u : dy.Signal, name : str = ''):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, 1 ] ).set_name(name + '_i')
    y = dy.delay( i).set_name(name + '_y')

    yFb << y

    return y


def diff( u : dy.Signal, name : str):

    i = dy.delay( u ).set_name(name + '_i')
    y = dy.add( [ i, u ], [ -1, 1 ] ).set_name(name + '_y')

    return y



def generate_signal_PWM( period, modulator ):

    number_of_samples_to_stay_in_A = period * modulator
    number_of_samples_to_stay_in_B = period * ( dy.float64(1) - modulator )

    number_of_samples_to_stay_in_A.set_name('number_of_samples_to_stay_in_A')
    number_of_samples_to_stay_in_B.set_name('number_of_samples_to_stay_in_B')

    with dy.sub_statemachine( "statemachine1" ) as switch:

        with switch.new_subsystem('state_on') as system:

            on = dy.float64(1.0).set_name('on')

            counter = dy.counter().set_name('counter')
            timeout = ( counter >= number_of_samples_to_stay_in_A ).set_name('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=1 ).set_name('next_state')

            system.set_switched_outputs([ on ], next_state)


        with switch.new_subsystem('state_off') as system:

            off = dy.float64(0.0).set_name('off')

            counter = dy.counter().set_name('counter')
            timeout = ( counter >= number_of_samples_to_stay_in_B ).set_name('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=0 ).set_name('next_state')

            system.set_switched_outputs([ off ], next_state)


    # define the outputs
    pwm = switch.outputs[0].set_name("pwm")
    state_control = switch.state.set_name('state_control')

    return pwm, state_control





#testname = 'system_state_machine_pwm' # 
testname = 'loop_yield_until' # 'signal_periodic_impulse' #'loop_until' #'inline_ifsubsystem_oscillator' # 

test_modification_1 = True  # option should not have an influence on the result
test_modification_2 = False # shall raise an error once this is true


if testname == 'test1':

    baseDatatype = dy.DataTypeFloat64(1) 

    U = dy.system_input( baseDatatype ).set_name('extU')

    y1 = firstOrderAndGain( U, 0.2, gain=0.8, name="1")
    y2 = firstOrderAndGain( y1, 0.2, gain=0.8, name="2")
    y3 = firstOrderAndGain( y2, 0.2, gain=0.8, name="3")

    E1 = dy.system_input( baseDatatype ).set_name('extE1')
    E2 = dy.system_input( baseDatatype ).set_name('extE2')

    y = dy.add( [ y3, E1, E2 ], [ 0.1, 0.2, 0.3] ).set_blockname('y (add)').set_name('y')

    # define the outputs of the simulation
    output_signals = [ y, y2 ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0
    input_signals_mapping[ E1 ] = 2.0
    input_signals_mapping[ E2 ] = 3.0



if testname == 'test_integrator':

    baseDatatype = dy.DataTypeFloat64(1) 

    U = dy.system_input( baseDatatype ).set_name('extU')

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

    U = dy.system_input( baseDatatype ).set_name('extU')

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).set_blockname('acc').set_name('acc')

    v << dy.euler_integrator( acc, Ts=0.1)
    x << dy.euler_integrator( v, Ts=0.1)

    # define the outputs of the simulation
    output_signals = [ x, v ]

    # specify what the input signals shall be in the runtime
    input_signals_mapping = {}
    input_signals_mapping[ U ] = 1.0


if testname == 'oscillator_modulation_example':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    #loop_iterations = dy.system_input( baseDatatype ).set_name('loop_iterations').set_properties({ "range" : [0, 100], "default_value" : 20 })
    U = dy.system_input( baseDatatype ).set_name('osc_excitement').set_properties({ "range" : [0, 4.0], "default_value" : 0.0 })
    osc_pos_feedback_gain = dy.system_input( baseDatatype ).set_name('osc_pos_feedback_gain').set_properties({ "range" : [0, 0.1], "default_value" : 0.0025 })
    osc_vel_feedback_gain = dy.system_input( baseDatatype ).set_name('osc_vel_feedback_gain').set_properties({ "range" : [0, 0.5], "default_value" : 0.018 })

    # model
    x = dy.signal()
    v = dy.signal()

    acc = U - osc_vel_feedback_gain * v - osc_pos_feedback_gain * x

    v << dy.euler_integrator( acc, Ts=0.1, initial_state=-1.0 )
    x << dy.euler_integrator( v, Ts=0.1 )
    
    # main simulation ouput
    output_signals = [ x, v ]

    input_signals_mapping = {}



if testname == 'test_oscillator_controlled':

    import TestLibray as TestLibray
    library_entries.append( TestLibray.oscillator )


    baseDatatype = dy.DataTypeFloat64(1) 

    # input to simulations

    Kp = dy.system_input( baseDatatype ).set_name('Kp') # 0.3
    Kd = dy.system_input( baseDatatype ).set_name('Kd') # 0.3
    Ki = dy.system_input( baseDatatype ).set_name('Ki') # 0.3
    reference = dy.system_input( baseDatatype ).set_name('ref') # 1.0)

    # 
    controlledVariableFb = dy.signal()

    # control error
    controlError = dy.add( [ reference, controlledVariableFb ], [ 1, -1 ] ).set_name('err')

    # P
    u_p = dy.operator1( [ Kp, controlError ], '*' ).set_name('u_p')

    # D
    d = diff( controlError, 'PID_D')
    u_d = dy.operator1( [ Kd, d ], '*' ).set_name('u_d')

    # I
    u_i_tmp = dy.signal()
    u_i = dy.delay(controlError + u_i_tmp) * Ki

    u_i_tmp << u_i

    u_i_tmp.set_name('u_i')

    if test_modification_1:
        u_i = u_i_tmp

    # sum up
    if not test_modification_2:
        controlVar = u_p + u_d + u_i  # TODO: compilation fails if u_i is removed because u_i is not connected to sth.

    else:
        # shall raise an error
        anonymous_signal = dy.signal()
        controlVar = u_p + u_d + u_i + anonymous_signal

    controlVar.set_name('u')

    # stupid test
    fancyVariable = controlVar - dy.const( 2.5, baseDatatype ) / dy.const( 1.5, baseDatatype )

    # plant starts here
    U = controlVar

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -1.1, -0.1 ] ).set_blockname('acceleration model')

    v << dy.euler_integrator( acc, Ts=0.1)
    x << dy.euler_integrator( v, Ts=0.1)

    # x is the controlled variable
    controlledVariableFb << x
    
    # define the outputs of the simulation
    x.set_name('x')
    v.set_name('v')
    output_signals = [ x,v ]

if testname == 'basic':

    baseDatatype = dy.DataTypeFloat64(1) 
    U = dy.system_input( baseDatatype ).set_name('input')

    x1 = dy.delay(U)

    output_signals = [ x1 ]






if testname == 'test_comparison':

    baseDatatype = dy.DataTypeFloat64(1) 
    u1 = dy.system_input( baseDatatype ).set_name('u1')
    u2 = dy.system_input( baseDatatype ).set_name('u2')

    isGreater = dy.comparison(left = u1, right = u2, operator = '>' )

    # NOTE: intentionally only x is the output. v is intentionally unused in this test.
    output_signals = [ isGreater ]



if testname == 'test_step':
    y = dy.float64(3) * dy.signal_step(10) + dy.float64(-5) * dy.signal_step(40) + dy.float64(2) * dy.signal_step(70) 

    output_signals = [ y ]


if testname == 'test_ramp':
    y1 = dy.float64(3) * dy.signal_ramp(10) - dy.float64(2) * dy.signal_ramp(70) 
    y2 = dy.float64(-5) * dy.signal_ramp(40)

    y1.set_name('y1')

    output_signals = [ y1, y2 ]



if testname == 'test_datatype_convertion':
    y = dy.int32(333)

    y = dy.convert(y, dy.DataTypeFloat64(1) )
    
    output_signals = [ y ]


if testname == 'dtf_lowpass_1_order':

    u = dy.float64(1.0)

    y = dy.dtf_lowpass_1_order(u, z_infinity=0.95 )
    
    output_signals = [ y ]


if testname == 'dtf_lowpass_1_order_V2':

    u = dy.float64(1.0)

    y1 = dy.dtf_lowpass_1_order(u,  z_infinity=0.97 ).set_name('_1st_order')
    y2 = dy.dtf_lowpass_1_order(y1, z_infinity=0.97 ).set_name('_2nd_order')
    y3 = dy.dtf_lowpass_1_order(y2, z_infinity=0.97 ).set_name('_3rd_order')
    y4 = dy.dtf_lowpass_1_order(y3, z_infinity=0.97 ).set_name('_4th_order')
    y5 = dy.dtf_lowpass_1_order(y4, z_infinity=0.97 ).set_name('_5th_order')
    
    output_signals = [ y1, y2, y3, y4, y5 ]


if testname == 'transfer_function_discrete':

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

    # convert the transfer function T to the representation needed for dy.transfer_function_discrete
    b, a = get_zm1_coeff(T)

    # system input
    u = dy.float64(1.0)

    # implement the transfer function
    y = dy.transfer_function_discrete(u, num_coeff=b, den_coeff=a ).set_name('y')
    

    output_signals = [ y ]


if testname == 'switchNto1':
    switch_state = dy.system_input( dy.DataTypeInt32(1) ).set_name('switch_state')

    u1 = dy.float64(1.0)
    u2 = dy.float64(2.0)
    u3 = dy.float64(3.0)
    u4 = dy.float64(4.0)

    y = dy.switchNto1( state=switch_state, inputs=[u1,u2,u3,u4] )
    
    output_signals = [ y ]




# NOTE: is this test still valid?  
if testname == 'inline_subsystem':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    switch = dy.system_input( baseDatatype ).set_name('switch')
    input = dy.system_input( baseDatatype ).set_name('input')


    with dy.sub() as system:

        # the signal 'input' is automatically detected to be an input to the subsystem

        tmp = dy.float64(2.5).set_name('const25')

        output = input * tmp 

        output.set_name('output_of_if')
        output = system.add_output(output)

        output.set_name("embedder_output")


    # optional y = output
    y = dy.float64(10.0) * output

    # main simulation ouput
    output_signals = [ y ]








if testname == 'loop_yield':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    #loop_iterations = dy.system_input( baseDatatype ).set_name('loop_iterations').set_properties({ "range" : [0, 100], "default_value" : 20 })
    U = dy.system_input( baseDatatype ).set_name('osc_excitement').set_properties({ "range" : [0, 4.0], "default_value" : 0.0 })
    osc_pos_feedback_gain = dy.system_input( baseDatatype ).set_name('osc_pos_feedback_gain').set_properties({ "range" : [0, 0.1], "default_value" : 0.0025 })
    osc_vel_feedback_gain = dy.system_input( baseDatatype ).set_name('osc_vel_feedback_gain').set_properties({ "range" : [0, 0.5], "default_value" : 0.018 })
    subsample_period = dy.system_input( baseDatatype ).set_name('subsample_period').set_properties({ "range" : [0, 25], "default_value" : 10 })

    with dy.sub_loop( max_iterations=1000 ) as system:

        x = dy.signal()
        v = dy.signal()

        acc = U - osc_vel_feedback_gain * v - osc_pos_feedback_gain * x

        v << dy.euler_integrator( acc, Ts=0.1, initial_state=-1.0 )
        x << dy.euler_integrator( v, Ts=0.1 )
        
        system.set_outputs([ x, v ])
        system.loop_yield( dy.signal_periodic_impulse(period=subsample_period, phase=2) )

    output_x = system.outputs[0]
    output_v = system.outputs[1]

    # main simulation ouput
    output_signals = [ output_x, output_v ]





if testname == 'loop_until':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    loop_iterations = dy.system_input( baseDatatype ).set_name('loop_iterations').set_properties({ "range" : [0, 100], "default_value" : 20 })

    with dy.sub_loop( max_iterations=80 ) as system:
        
        system.set_outputs([ dy.counter() ])

        system.loop_until( dy.counter() >= loop_iterations )

    counter = system.outputs[0]

    # main simulation ouput
    output_signals = [ counter ]




if testname == 'loop_yield_until':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    loop_iterations = dy.system_input( baseDatatype ).set_name('loop_iterations').set_properties({ "range" : [0, 500], "default_value" : 100 })
    subsample_period = dy.system_input( baseDatatype ).set_name('subsample_period').set_properties({ "range" : [0, 25], "default_value" : 10 })

    with dy.sub_loop( max_iterations=80 ) as system:
        
        system.set_outputs([ dy.counter() ])

        system.loop_yield( dy.signal_periodic_impulse(period=subsample_period, phase=0) )
        system.loop_until( dy.counter() >= loop_iterations )

    counter = system.outputs[0]

    # main simulation ouput
    output_signals = [ counter ]








if testname == 'inline_ifsubsystem_oscillator':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    activation_sample = dy.system_input( baseDatatype ).set_name('activation_sample').set_properties({ "range" : [0, 100], "default_value" : 20 })
    U = dy.system_input( baseDatatype ).set_name('osc_excitement').set_properties({ "range" : [0, 4.0], "default_value" : 0.5 })

    with dy.sub_if( (dy.signal_ramp(0) > activation_sample) * (dy.signal_ramp(100) < activation_sample), prevent_output_computation=False ) as system:

        x = dy.signal()
        v = dy.signal()

        acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).set_blockname('acc').set_name('acc')

        v << dy.euler_integrator( acc, Ts=0.1, initial_state=-1.0 )
        x << dy.euler_integrator( v, Ts=0.1)
        
        system.set_outputs([ x, v ])

    output_x = system.outputs[0]
    output_v = system.outputs[1]

    # main simulation ouput
    output_signals = [ output_x, output_v ]







if testname == 'inline_ifsubsystem':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    switch = dy.system_input( baseDatatype ).set_name('switch_condition').set_properties({ "range" : [0, 200], "default_value" : 10 }) 
    input_signal = dy.system_input( baseDatatype ).set_name('input')


    ramp = dy.signal_ramp(10).set_name('ramp')

    activated = ramp > switch
    activated.set_name( 'activated' )

    with dy.sub_if( activated ) as system:

        # the signal 'input' is automatically detected to be an input to the subsystem

        tmp = dy.float64(2.5).set_name('const25')

        

        output = input_signal * tmp + dy.counter()

        output.set_name('output_of_if')
        
        # output = system.add_output(output)
        # output.set_name("embedder_output")

        system.set_outputs([ output ])

    output = system.outputs[0]

    # optional y = output
    y = dy.float64(10.0) * output

    # main simulation ouput
    output_signals = [ y, ramp ]





if testname == 'system_switch':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    active_system = dy.system_input( dy.DataTypeInt32(1) ).set_name('active_system')
    U = dy.system_input( baseDatatype ).set_name('osc_excitement')

    with dy.sub_switch( "switch1", active_system ) as switch:

        with switch.new_subsystem('default_system') as system: # NOTE: do not put c++ keywords as system names
            # this is defined to be the default subsystem
            # the datatypes of the outputs defined here a
            # used for the main outputs of the function 
            # dy.sub_switch

            # inputs are [] (no inputs)

            x = dy.float64(0.0).set_name('x_def')
            v = dy.float64(0.0).set_name('v_def')

            system.set_switched_outputs([ x, v ])
                    

        with switch.new_subsystem('running_system') as system:
            # inputs are [U]

            x = dy.signal()
            v = dy.signal()

            acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).set_blockname('acc').set_name('acc')

            v << dy.euler_integrator( acc, Ts=0.1, initial_state=-1.0 )
            x << dy.euler_integrator( v,   Ts=0.1 )

            system.set_switched_outputs([ x, v ])


            #  python3 -m http.server

    output_x = switch.outputs[0].set_name("ox")
    output_v = switch.outputs[1].set_name("ov")

    # main simulation ouput
    output_signals = [ output_x, output_v ]









if testname == 'system_state_machine':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    U2 = dy.system_input( baseDatatype ).set_name('osc_excitement')

    U = U2 * dy.float64(1.234)
    U.set_name("stachmachine_input_U")

    with dy.sub_statemachine( "statemachine1" ) as switch:


        with switch.new_subsystem('state_A') as system: # NOTE: do not put c++ keywords as system names

            x = dy.float64(0.0).set_name('x_def')
            v = dy.float64(0.0).set_name('v_def')


            counter = dy.counter().set_name('counter')
            timeout = ( counter > dy.int32(10) ).set_name('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=1 ).set_name('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)


        with switch.new_subsystem('state_B') as system:

            x = dy.signal()
            v = dy.signal()

            acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).set_blockname('acc').set_name('acc')

            v << dy.euler_integrator( acc, Ts=0.1, initial_state=-1.0 )
            x << dy.euler_integrator( v,   Ts=0.1 )

            counter = dy.counter().set_name('counter')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=counter > dy.int32(50), new_value=0 ).set_name('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)



    output_x = switch.outputs[0].set_name("ox")
    output_v = switch.outputs[1].set_name("ov")
    counter = switch.outputs[2].set_name("counter")

    state = switch.state.set_name('state_control')

    # main simulation ouput
    output_signals = [ output_x, output_v, state, counter ]









if testname == 'system_state_machine2':

    baseDatatype = dy.DataTypeFloat64(1) 

    # define system inputs
    number_of_samples_to_stay_in_A = dy.system_input( baseDatatype ).set_name('number_of_samples_to_stay_in_A')
    threshold_for_x_to_leave_B     = dy.system_input( baseDatatype ).set_name('threshold_for_x_to_leave_B')
    U2                             = dy.system_input( baseDatatype ).set_name('osc_excitement')

    # some modification of one input
    U = U2 * dy.float64(1.234)
    U.set_name("stachmachine_input_U")

    with dy.sub_statemachine( "statemachine1" ) as switch:

        with switch.new_subsystem('state_A') as system:

            # implement a dummy system the produces zero values for x and v
            x = dy.float64(0.0).set_name('x_def')
            v = dy.float64(0.0).set_name('v_def')

            counter = dy.counter().set_name('counter')
            timeout = ( counter > number_of_samples_to_stay_in_A ).set_name('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=1 ).set_name('next_state')

            system.set_switched_outputs([ x, v, counter ], next_state)


        with switch.new_subsystem('state_B') as system:

            # implement a simple spring-mass oscillator: 
            # x is the position, v is the velocity, acc is the acceleration

            # create placeholder symbols for x and v (as they are used before being defined)
            x = dy.signal()
            v = dy.signal()

            acc = dy.add( [ U, v, x ], [ 1, -0.1, -0.1 ] ).set_blockname('acc').set_name('acc')

            # close the feedback loops for x and v
            v << dy.euler_integrator( acc, Ts=0.1, initial_state=-1.0 )
            x << dy.euler_integrator( v,   Ts=0.1 )

            leave_this_state = (x > threshold_for_x_to_leave_B).set_name("leave_this_state")
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=leave_this_state, new_value=0 ).set_name('next_state')

            counter = dy.counter().set_name('counter')

            system.set_switched_outputs([ x, v, counter ], next_state)


    # define the outputs
    output_x      = switch.outputs[0].set_name("ox")
    output_v      = switch.outputs[1].set_name("ov")
    counter       = switch.outputs[2].set_name("counter")
    state_control = switch.state.set_name('state_control')

    # main simulation ouput
    output_signals = [ output_x, output_v, state_control, counter ]







if testname == 'system_state_machine_pwm':

    baseDatatype = dy.DataTypeFloat64(1) 

    # define system inputs
    period = dy.system_input( baseDatatype ).set_name('period')
    modulator = dy.system_input( baseDatatype ).set_name('modulator') * dy.float64(1.0/100)

    # implement the generator
    pwm, state_control = generate_signal_PWM( period, modulator )

    # lowpass
    output = firstOrderAndGain( pwm, z_inf=0.9, gain=0.1)

    # main simulation ouput
    output_signals = [ output, state_control ]








if testname == 'nested_state_machine':

    baseDatatype = dy.DataTypeFloat64(1) 

    # define system inputs
    number_of_samples_to_stay_in_A = dy.system_input( baseDatatype ).set_name('number_of_samples_to_stay_in_A')
    number_of_samples_to_stay_in_B = dy.system_input( baseDatatype ).set_name('number_of_samples_to_stay_in_B')

    period    = dy.system_input( baseDatatype ).set_name('pwm_period')
    modulator = dy.system_input( baseDatatype ).set_name('pwm_modulator') * dy.float64(1.0/100)

    with dy.sub_statemachine( "outer_statemachine" ) as switch:

        with switch.new_subsystem('state_A') as system:

            # implement a dummy system that produces zero values for x and v
            output = dy.float64(0.0).set_name('output')

            counter = dy.counter().set_name('counter')
            timeout = ( counter >= number_of_samples_to_stay_in_A ).set_name('timeout')
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=timeout, new_value=1 ).set_name('next_state')

            system.set_switched_outputs([ output ], next_state)


        with switch.new_subsystem('state_B') as system:

            # nested state machine
            output, state_control = generate_signal_PWM( period, modulator )

            counter = dy.counter().set_name('counter')
            leave_this_state = (counter >= number_of_samples_to_stay_in_B).set_name("leave_this_state")
            next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=leave_this_state, new_value=0 ).set_name('next_state')

            system.set_switched_outputs([ output ], next_state)


    # define the outputs
    signal        = switch.outputs[0].set_name("signal")
    state_control = switch.state.set_name('state_control')

    # lowpass
    #output = firstOrderAndGain( signal, z_inf=0.9, gain=0.1)

    output_1 = dy.dtf_lowpass_1_order(signal,  z_infinity=0.9 )
    output = dy.dtf_lowpass_1_order(output_1,  z_infinity=0.9 )

    # main simulation ouput
    output_signals = [ signal, output, state_control ]



if testname == 'memory':

    import math

    #vector = np.linspace(-1.11, 2.22, 400)

    it = np.linspace(0,1, 400)
    vector = np.sin( 10 * it * math.pi ) + it


    data = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=vector ).set_name('data')


    looked_up_element = dy.memory_read( memory=data, index=dy.counter() ).set_name('looked_up_element')
    
    looked_up_element_delayed = dy.delay( dy.memory_read( memory=data, index=dy.counter() ) ).set_name('looked_up_element_delayed')

    output_signals = [ looked_up_element, looked_up_element_delayed ]




if testname == 'memory_machine':

    vector = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 3 ]
    data = dy.memory(datatype=dy.DataTypeInt32(1), constant_array=vector ).set_name('data')

    position_index = dy.signal()
    next_position = dy.memory_read( memory=data, index=position_index )
    position_index << dy.delay( next_position )

    output_signals = [ position_index, next_position ]


if testname == 'memory_ringbuf':

    vector = [ 2.2, 2.1, 2.3, 2.6, 2.3, 2.8, 2.3, 2.4, 2.9, 2.0 ]

    rolling_index = dy.counter_limited( upper_limit=len(vector)-1, stepwidth=dy.int32(1), initial_state=1, reset_on_limit=True)
    write_index = dy.delay(rolling_index)
    value_to_write = dy.signal_sinus(N_period=150)

    data = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=vector, write_index=write_index, value=value_to_write ).set_name('data')
    looked_up_element = dy.memory_read( memory=data, index=rolling_index ).set_name('looked_up_element')

    output_signals = [ value_to_write, looked_up_element, rolling_index ]

if testname == 'play':

    vector = np.linspace(0.1,0.9,20)

    play1, index = dy.play( sequence_array=vector, reset=dy.signal_impulse(k_event=50), reset_on_end=False, prevent_initial_playback=True )

    play2, index = dy.play( sequence_array=vector, reset=dy.signal_impulse(k_event=50), reset_on_end=False, prevent_initial_playback=False )

    play3, index = dy.play( sequence_array=vector, reset_on_end=True )

    output_signals = [ play1, play2, play3 ]



if testname == 'generic_cpp_static':

    baseDatatype = dy.DataTypeFloat64(1) 

    # define system inputs
    someinput = dy.system_input( baseDatatype ).set_name('someinput')


    value = dy.float64(0.7)

    #
    source_code = """

        // c++ code

        output1 = value;
        if (someinput > value) {
            output2 = value;
        } else {
            output2 = someinput;
        }
        output3 = 0.0;

    """

    outputs = dy.generic_cpp_static(input_signals=[ someinput, value ], input_names=[ 'someinput', 'value' ], 
                        input_types=[ dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ], 
                        output_names=['output1', 'output2', 'output3'],
                        output_types=[ dy.DataTypeFloat64(1), dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ],
                        cpp_source_code = source_code )

    output1 = outputs[0]
    output2 = outputs[1]
    output3 = outputs[2]

    dy.set_primary_outputs( [ output1, output2, output3 ], ['output1', 'output2', 'output3'] )
    
    output_signals = None





if testname == 'signal_periodic_impulse':
    
    baseDatatype = dy.DataTypeFloat64(1) 

    phase = dy.system_input( baseDatatype ).set_name('phase').set_properties({ "range" : [0, 25], "default_value" : 0 })
    period = dy.system_input( baseDatatype ).set_name('period').set_properties({ "range" : [0, 25], "default_value" : 10 })

    pulses = dy.signal_periodic_impulse(period=period, phase=phase)

    # main simulation ouput
    output_signals = [ pulses ]





if testname == 'vanderpol':
    # https://en.wikipedia.org/wiki/Van_der_Pol_oscillator

    pass



#
#
# general
#
#




# set the outputs of the system
if output_signals is not None:
    dy.set_primary_outputs(output_signals)

# Compile system (propagate datatypes)
compile_results = dy.compile_current_system()


# Build an executable based on a template
input_signals_mapping = {}
runtime_template = dy.WasmRuntime(input_signals_mapping=input_signals_mapping)
runtime_template.set_compile_results(compile_results)

#runtime_template = dy.PutBasicRuntimeCpp(input_signals_mapping=input_signals_mapping)


# optional: add (pre-compiled) systems from the libraries
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


