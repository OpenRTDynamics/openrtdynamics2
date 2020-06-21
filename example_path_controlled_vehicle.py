import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)

import math

import numpy as np

# nice functions to create paths
def co(time, val, Ts=1.0):
    return val * np.ones(int(math.ceil(time / Ts)))


def cosra(time, val1, val2, Ts=1.0):
    N = int(math.ceil(time / Ts))
    return val1 + (val2-val1) * (0.5 + 0.5 * np.sin(math.pi * np.linspace(0, 1, N) - math.pi/2))


def ra(time, val1, val2, Ts=1.0):
    N = int(math.ceil(time / Ts))
    return np.linspace(val1, val2, N)



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



def lookup_distance_index( path_distance_storage, path_x_storage, path_y_storage, distance ):
    #
    source_code = """
        index = 0;
        int i = 0;

        for (i = 0; i < 100; ++i ) {
            if ( path_distance_storage[i] < distance && path_distance_storage[i+1] > distance ) {
                index = i;
                break;
            }
        }
    """
    array_type = dy.DataTypeArray( 360, datatype=dy.DataTypeFloat64(1) )
    outputs = dy.generic_cpp_static(input_signals=[ path_distance_storage, path_x_storage, path_y_storage, distance ], 
                                    input_names=[ 'path_distance_storage', 'path_x_storage', 'path_y_storage', 'distance' ], 
                                    input_types=[ array_type, array_type, array_type, dy.DataTypeFloat64(1) ], 
                                    output_names=['index'],
                                    output_types=[ dy.DataTypeInt32(1) ],
                                    cpp_source_code = source_code )

    index = outputs[0]

    return index


def lookup_closest_point( path_distance_storage, path_x_storage, path_y_storage, x, y ):
    #
    source_code = """
        // int N = 360;
        int N = *(&path_distance_storage + 1) - path_distance_storage;

        int i = 0;
        double min_distance_to_path = 1000000;
        int min_index = 0;

        for (i = 0; i < N; ++i ) {
            double dx = path_x_storage[i] - x_;
            double dy = path_y_storage[i] - y_;
            double distance_to_path = sqrt( dx * dx + dy * dy );

            if ( distance_to_path < min_distance_to_path ) {
                min_distance_to_path = distance_to_path;
                min_index = i;
            }
        }

        double dx_p1, dy_p1, dx_p2, dy_p2, distance_to_path_p1, distance_to_path_p2;

        dx_p1 = path_x_storage[min_index + 1] - x_;
        dy_p1 = path_y_storage[min_index + 1] - y_;
        distance_to_path_p1 = sqrt( dx_p1 * dx_p1 + dy_p1 * dy_p1 );

        dx_p2 = path_x_storage[min_index - 1] - x_;
        dy_p2 = path_y_storage[min_index - 1] - y_;
        distance_to_path_p2 = sqrt( dx_p2 * dx_p2 + dy_p2 * dy_p2 );

        int interval_start, interval_stop;
        if (distance_to_path_p1 < distance_to_path_p2) {
            // minimal distance in interval [min_index, min_index + 1]
            interval_start = min_index;
            interval_stop  = min_index + 1;
        } else {
            // minimal distance in interval [min_index - 1, min_index]
            interval_start = min_index - 1;
            interval_stop  = min_index;
        }

        // linear interpolation
        double dx = path_x_storage[interval_stop] - path_x_storage[interval_start] ;
        double dy = path_y_storage[interval_stop] - path_y_storage[interval_start] ;



        index_start   = interval_start;
        index_closest = min_index;
        Delta_l       = min_distance_to_path;

    """
    array_type = dy.DataTypeArray( 360, datatype=dy.DataTypeFloat64(1) )
    outputs = dy.generic_cpp_static(input_signals=[ path_distance_storage, path_x_storage, path_y_storage, x, y ], 
                                    input_names=[ 'path_distance_storage', 'path_x_storage', 'path_y_storage', 'x_', 'y_' ], 
                                    input_types=[ array_type, array_type, array_type, dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ], 
                                    output_names=[ 'index_closest', 'index_start', 'Delta_l'],
                                    output_types=[ dy.DataTypeInt32(1), dy.DataTypeInt32(1), dy.DataTypeFloat64(1) ],
                                    cpp_source_code = source_code )

    index_start = outputs[0]
    index_closest = outputs[1]
    Delta_l     = outputs[2]

    return index_closest, Delta_l, index_start





# define system inputs
velocity       = dy.system_input( baseDatatype ).set_name('velocity')   * dy.float64(0.2)
k_p            = dy.system_input( baseDatatype ).set_name('k_p')        * dy.float64(0.0005)

wheelbase = 3.0

# generate a step-wise reference signal
# pwm_signal, state_control = generate_signal_PWM( period=dy.float64(200), modulator=dy.float64(0.5) )
# reference = (pwm_signal - dy.float64(0.5)) * dy.float64(1.0)


path_x = np.concatenate(( ra(360, 0, 80),  )) 
path_y = np.concatenate(( co(50, 0), cosra(100, 0, 1), co(50, 1), cosra(100, 1, 0), co(60,0) ))
path_distance = np.concatenate((np.zeros(1), np.cumsum( np.sqrt( np.square( np.diff(path_x) ) + np.square( np.diff(path_y) ) ) ) ))

# distance[0] = 0.0
# for i in range(1, len(path_x)):

#     distance[i] = math.pow( path_x[i] - path_x[i-1], 2 ) 


path_x_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=path_x )
path_y_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=path_y )
path_distance_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=path_distance )

#
def sample_path(path_distance_storage, path_x_storage, path_y_storage, index):

    y1 = dy.memory_read( memory=path_y_storage, index=index ) 
    y2 = dy.memory_read( memory=path_y_storage, index=index + dy.int32(1) )

    x1 = dy.memory_read( memory=path_x_storage, index=index ) 
    x2 = dy.memory_read( memory=path_x_storage, index=index + dy.int32(1) )

    Delta_x = x2 - x1
    Delta_y = y2 - y1

    psi_r = dy.atan2(Delta_y, Delta_x)
    x_r = x1
    y_r = y1

    return x_r, y_r, psi_r

#
#x_r, y_r, psi_r = sample_path(path_distance_storage, path_x_storage, path_y_storage, index=dy.counter() )


distance = dy.ramp(k_start=0) * dy.float64(0.02)
# distance.set_datatype( dy.DataTypeFloat64(1) )
index = lookup_distance_index( path_distance_storage, path_x_storage, path_y_storage, distance )



#
reference = dy.memory_read( memory=path_y_storage, index=dy.counter() )

# create placeholder for the plant output signal
x   = dy.signal()
y   = dy.signal()
psi = dy.signal()

# lookup lateral distance to path
index_closest, Delta_l, index_start = lookup_closest_point( path_distance_storage, path_x_storage, path_y_storage, x, y )

x_r, y_r, psi_r = sample_path(path_distance_storage, path_x_storage, path_y_storage, index=index_closest )

# add sign information to the distance
psi_tmp = dy.atan2(y - y_r, x - x_r)
delta_angle = psi_r - psi_tmp # attention!
sign = dy.conditional_overwrite(dy.float64(1.0), delta_angle > dy.float64(0) ,  -1.0  )
Delta_l = Delta_l * sign





# controller error
error = reference - Delta_l

# steering = dy.float64(0.0) + k_p * error - psi
steering = psi_r - psi - k_p * Delta_l


#
# The model of the vehicle
#

# def triggered_ramp():
#    switchNto1( state : SignalUserTemplate, inputs : SignalUserTemplate )

#


def play( sequence_array, reset ):
    sequence_array_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=sequence_array )

    subsampling = dy.int32(1)
    playback_index = dy.signal()
    reached_end = playback_index == dy.int32(np.size(sequence_array))

    # increase the index counter until the end is reached
    new_index = playback_index + dy.conditional_overwrite(subsampling, reached_end , 0)

    # reset
    new_index = dy.conditional_overwrite(new_index, reset, 0)

    # introduce a state variable for the counter
    playback_index << dy.delay( new_index, initial_state=np.size(sequence_array) )

    # sample the given data
    output = dy.memory_read(sequence_array_storage, playback_index)

    return output, playback_index



#
amplitude = np.deg2rad( 0.6 )
steering_disturbance = np.concatenate(( cosra(50, 0, amplitude), co(10, amplitude), cosra(50, amplitude, 0) ))
steering_disturbance, i = play(steering_disturbance, reset=dy.counter() == dy.int32(50))


#steering_disturbance = ( dy.step(k_step=int(1.5*100)) - dy.step(k_step=int(2.0*100)) ) * dy.float64( np.deg2rad( -0.6 ) )

disturbes_steering = steering + steering_disturbance

x_dot   = velocity * dy.cos( disturbes_steering + psi )
y_dot   = velocity * dy.sin( disturbes_steering + psi )
psi_dot = velocity / dy.float64(wheelbase) * dy.sin( disturbes_steering )


# integrators
sampling_rate = 0.01
x    << euler_integrator(x_dot,   sampling_rate, 0.0)
y    << euler_integrator(y_dot,   sampling_rate, 0.0)
psi  << euler_integrator(psi_dot, sampling_rate, 0.0)

# main simulation ouput
dy.set_primary_outputs([ x, y, x_r, y_r, psi, reference, psi_r, steering, error, Delta_l, index_start, steering_disturbance ], 
        ['x', 'y', 'x_r', 'y_r', 'psi', 'reference', 'psi_r', 'steering', 'error', 'Delta_l__', 'lookup_index', 'steering_disturbance'])

# dy.set_primary_outputs([ reference, psi_r, Delta_x, Delta_y ], [ 'reference', 'psi_r', 'Delta_x', 'Delta_y'])


sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(), folder="generated/", build=True)

# print the sourcecode (main.cpp)
print(Style.DIM + sourcecode)

dy.clear()
