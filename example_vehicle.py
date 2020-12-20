import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)

import math



#
# define a PWM signal generator
#

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



#
# Solving a state space model of a vehicle
#
# 
#
system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 

# define a function that implements a discrete-time integrator
def euler_integrator( u : dy.Signal, sampling_rate : float, initial_state = 0.0):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, sampling_rate ] )
    y = dy.delay( i, initial_state )

    yFb << y

    return y


# define system inputs
velocity       = dy.system_input( baseDatatype ).set_name('velocity').set_properties({ "range" : [0, 20.0], "default_value" : 20.0 })
k_p            = dy.system_input( baseDatatype ).set_name('k_p').set_properties({ "range" : [0, 1.0], "default_value" : 0.33 })

wheelbase = 3.0

# generate a step-wise reference signal
pwm_signal, state_control = generate_signal_PWM( period=dy.float64(200), modulator=dy.float64(0.5) )
reference = (pwm_signal - dy.float64(0.5)) * dy.float64(1.0)

# create placeholder for the plant output signal
x   = dy.signal()
y   = dy.signal()
psi = dy.signal()

# controller error
error = reference - y

steering = dy.float64(0.0) + k_p * error - psi



x_dot   = velocity * dy.cos( steering + psi )
y_dot   = velocity * dy.sin( steering + psi )
psi_dot = velocity / dy.float64(wheelbase) * dy.sin( steering )



# integrators
sampling_rate = 0.01
x    << euler_integrator(x_dot,   sampling_rate, 0.0)
y    << euler_integrator(y_dot,   sampling_rate, 0.0)
psi  << euler_integrator(psi_dot, sampling_rate, 0.0)

# main simulation ouput
dy.set_primary_outputs([ x, y, psi, reference, steering, error ], ['x', 'y', 'psi', 'refrence', 'steering', 'error'])



sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(), folder="generated/", build=True)

# print the sourcecode (main.cpp)
print(Style.DIM + sourcecode)

dy.clear()
