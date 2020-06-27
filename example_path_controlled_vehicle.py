import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)

import math
import numpy as np

from vehicle_lib import *




#
# Solving a state space model of a vehicle
#
# 
#
system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 





# define system inputs
velocity       = dy.system_input( baseDatatype ).set_name('velocity').set_properties({ "range" : [0, 50], "unit" : "m/s", "default_value" : 17.0 })
k_p            = dy.system_input( baseDatatype ).set_name('k_p').set_properties({ "range" : [0, 4.0], "default_value" : 1.0 })
k_i            = dy.system_input( baseDatatype ).set_name('k_i').set_properties({ "range" : [0, 4.0], "default_value" : 0 })
k_d            = dy.system_input( baseDatatype ).set_name('k_d').set_properties({ "range" : [0, 0.05], "default_value" : 0 })

sample_disturbance     = dy.convert(dy.system_input( baseDatatype ).set_name('sample_disturbance').set_properties({ "range" : [0, 300], "unit" : "samples", "default_value" : 50 }), target_type=dy.DataTypeInt32(1) )
disturbance_amplitude  = dy.system_input( baseDatatype ).set_name('disturbance_amplitude').set_properties({ "range" : [0, 45], "unit" : "degrees", "default_value" : 5 })     * dy.float64(math.pi / 180.0)

wheelbase = 3.0

#
# define the path
#

Td = 0.1
path_x = np.concatenate(( ra(360, 0, 80, Ts=Td),  )) 
path_y = np.concatenate(( co(50, 0, Ts=Td), cosra(100, 0, 1, Ts=Td), co(50, 1, Ts=Td), cosra(100, 1, 0, Ts=Td), co(60,0, Ts=Td) ))
path_distance = np.concatenate((np.zeros(1), np.cumsum( np.sqrt( np.square( np.diff(path_x) ) + np.square( np.diff(path_y) ) ) ) ))
N_path = np.size(path_x)

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
Delta_u = dy.PID_controller(r=dy.float64(0.0), y=Delta_l, Ts=0.01, kp=k_p, ki = k_i, kd = k_d) # 

# path tracking
steering = psi_r - psi + Delta_u

#
# The model of the vehicle
#


#
disturbance_transient = np.concatenate(( cosra(50, 0, 1.0), co(10, 1.0), cosra(50, 1.0, 0) ))
steering_disturbance, i = dy.play(disturbance_transient, reset=dy.counter() == sample_disturbance)

# apply disturbance to the steering input
disturbed_steering = steering + steering_disturbance * disturbance_amplitude



# bicycle model
x_dot   = velocity * dy.cos( disturbed_steering + psi )
y_dot   = velocity * dy.sin( disturbed_steering + psi )
psi_dot = velocity / dy.float64(wheelbase) * dy.sin( disturbed_steering )

# integrators
sampling_rate = 0.01
x    << dy.euler_integrator(x_dot,   sampling_rate, 0.0)
y    << dy.euler_integrator(y_dot,   sampling_rate, 0.0)
psi  << dy.euler_integrator(psi_dot, sampling_rate, 0.0)




# main simulation ouput
dy.set_primary_outputs([ x, y, x_r, y_r, psi, psi_r, steering, Delta_l, index_start, steering_disturbance ], 
        ['x', 'y', 'x_r', 'y_r', 'psi', 'psi_r', 'steering', 'Delta_l__', 'lookup_index', 'steering_disturbance'])

#
sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(), folder="generated/", build=True)

# print the sourcecode (main.cpp)
#print(Style.DIM + sourcecode)

dy.clear()
