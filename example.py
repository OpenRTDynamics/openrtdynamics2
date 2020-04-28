import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)


#
# Enter a new system (simulation)
#
system = dy.enter_system('simulation')



# define a function that implements a discrete-time integrator
def euler_integrator( u : dy.Signal, Ts : float, name : str, initial_state = None):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, Ts ] ).set_name(name + '_i')
    y = dy.delay( i, initial_state ).set_name(name + '_y')

    yFb << y

    return y





baseDatatype = dy.DataTypeFloat64(1) 

# define system inputs
number_of_samples_to_stay_in_A = dy.system_input( baseDatatype ).set_name('number_of_samples_to_stay_in_A')
threshold_for_x_to_leave_B     = dy.system_input( baseDatatype ).set_name('threshold_for_x_to_leave_B')
U2                             = dy.system_input( baseDatatype ).set_name('osc_excitement')

# some modification of one input
U = U2 * dy.float64(1.234)
U.set_name("stachmachine_input_U")

with dy.sub_statemachine( "statemachine1" ) as switch:

    with switch.new_subsystem('state_A') as system: # NOTE: do not put c++ keywords as system names

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
        v << euler_integrator( acc, Ts=0.1, name="intV", initial_state=-1.0 )
        x << euler_integrator( v,   Ts=0.1, name="intX" )

        leave_this_state = (x > threshold_for_x_to_leave_B).set_name("leave_this_state")
        next_state = dy.conditional_overwrite(signal=dy.int32(-1), condition=leave_this_state, new_value=0 ).set_name('next_state')

        counter = dy.counter().set_name('counter')

        system.set_switched_outputs([ x, v, counter ], next_state)


# define the outputs
output_x      = switch.outputs[0].set_name("ox")
output_v      = switch.outputs[1].set_name("ov")
counter       = switch.outputs[2].set_name("counter")
state_control = switch.state.set_name('state_control')

# set the outputs of the system
dy.set_primary_outputs([ output_x, output_v, state_control, counter ])

# Compile system (propagate datatypes)
compile_results = dy.compile_current_system()

# Build an executable based on a template
runtime_template = dy.WasmRuntimeCpp(compile_results, input_signals_mapping={})
sourcecode, manifest = runtime_template.code_gen()

# print the sourcecode (main.cpp)
print(Style.DIM + sourcecode)

# write generated code into a folder and build
runtime_template.write_code("generated/")
runtime_template.build()
