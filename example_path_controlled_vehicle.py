import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)

import math
import numpy as np

from vehicle_lib.vehicle_lib import *
from vehicle_lib.path_generation import *

import vehicle_lib.example_data as example_data


#
# Solving a state space model of a vehicle
#
# 
#
system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 





# define system inputs
velocity       = dy.system_input( baseDatatype ).set_name('velocity').set_properties({ "range" : [0, 50], "unit" : "m/s", "default_value" : 23.75, "title" : "vehicle velocity" })
k_p            = dy.system_input( baseDatatype ).set_name('k_p').set_properties({ "range" : [0, 4.0], "default_value" : 0.112, "title" : "controller gain" })

disturbance_amplitude  = dy.system_input( baseDatatype ).set_name('disturbance_amplitude').set_properties({ "range" : [-45, 45], "unit" : "degrees", "default_value" : -45, "title" : "disturbance amplitude" })     * dy.float64(math.pi / 180.0)
sample_disturbance     = dy.convert(dy.system_input( baseDatatype ).set_name('sample_disturbance').set_properties({ "range" : [0, 300], "unit" : "samples", "default_value" : 0, "title" : "time of disturbance" }), target_type=dy.DataTypeInt32(1) )

wheelbase = 3.0

#
# define the path
#

Td = 0.1
path_x = example_data.output['X'] # np.concatenate(( ra(360, 0, 80, Ts=Td),  )) 
path_y = example_data.output['Y'] # np.concatenate(( co(50, 0, Ts=Td), cosra(100, 0, 1, Ts=Td), co(50, 1, Ts=Td), cosra(100, 1, 0, Ts=Td), co(60,0, Ts=Td) ))
path_distance = example_data.output['D'] #  np.concatenate((np.zeros(1), np.cumsum( np.sqrt( np.square( np.diff(path_x) ) + np.square( np.diff(path_y) ) ) ) ))
N_path = example_data.Nmax # np.size(path_x)

path_x_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=path_x )
path_y_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=path_y )
path_distance_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=path_distance )



# create placeholder for the plant output signal
x   = dy.signal()
y   = dy.signal()
psi = dy.signal()

# lookup lateral distance to path
index_closest, distance, index_start = lookup_closest_point( N_path, path_distance_storage, path_x_storage, path_y_storage, x, y )

# 
x_r, y_r, psi_r = sample_path(path_distance_storage, path_x_storage, path_y_storage, index=index_closest )

# add sign information to the distance
Delta_l = distance_to_Delta_l( distance, psi_r, x_r, y_r, x, y )



#
# controller
#

# feedback
Delta_u = dy.PID_controller(r=dy.float64(0.0), y=Delta_l, Ts=0.01, kp=k_p, ki = dy.float64(0.0), kd = dy.float64(0.0)) # 

# path tracking
steering = psi_r - psi + Delta_u
steering = dy.unwrap_angle(angle=steering, normalize_around_zero = True) 

# steering = dy.difference_angle(psi_r , psi) + Delta_u

#
# The model of the vehicle
#


#
disturbance_transient = np.concatenate(( cosra(50, 0, 1.0), co(10, 1.0), cosra(50, 1.0, 0) ))
steering_disturbance, i = dy.play(disturbance_transient, reset=dy.counter() == sample_disturbance, prevent_initial_playback=True)

# apply disturbance to the steering input
disturbed_steering = steering + steering_disturbance * disturbance_amplitude

#
disturbed_steering = dy.saturate(u=disturbed_steering, lower_limit=-math.pi/2.0, uppper_limit=math.pi/2.0)


def discrete_time_bicycle_model(delta, v):
    x   = dy.signal()
    y   = dy.signal()
    psi = dy.signal()

    # bicycle model
    x_dot   = v * dy.cos( delta + psi )
    y_dot   = v * dy.sin( delta + psi )
    psi_dot = v / dy.float64(wheelbase) * dy.sin( delta )

    # integrators
    sampling_rate = 0.01
    x    << dy.euler_integrator(x_dot,   sampling_rate, 0.0)
    y    << dy.euler_integrator(y_dot,   sampling_rate, 0.0)
    psi  << dy.euler_integrator(psi_dot, sampling_rate, 0.0)

    return x, y, psi


x_, y_, psi_ = discrete_time_bicycle_model(disturbed_steering, velocity)

x << x_
y << y_
psi << psi_

# main simulation ouput
dy.set_primary_outputs([ x, y, x_r, y_r, psi, psi_r, steering, Delta_l, index_start, steering_disturbance, disturbed_steering ], 
        ['x', 'y', 'x_r', 'y_r', 'psi', 'psi_r', 'steering', 'Delta_l__', 'lookup_index', 'steering_disturbance', 'disturbed_steering'])

#
sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(), folder="generated/", build=True)

# print the sourcecode (main.cpp)
#print(Style.DIM + sourcecode)

dy.clear()
