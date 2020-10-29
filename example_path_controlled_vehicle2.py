import openrtdynamics2.lang as dy

import os
# 
import math
import numpy as np

from vehicle_lib.vehicle_lib import *
import vehicle_lib.example_data as example_data


#
# A vehicle controlled to follow a given path 
#

system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 

# define simulation inputs
velocity       = dy.system_input( baseDatatype ).set_name('velocity').set_properties({ "range" : [0, 50], "unit" : "m/s", "default_value" : 23.75, "title" : "vehicle velocity" })
k_p            = dy.system_input( baseDatatype ).set_name('k_p').set_properties({ "range" : [0, 4.0], "default_value" : 0.112, "title" : "controller gain" })

disturbance_amplitude  = dy.system_input( baseDatatype ).set_name('disturbance_amplitude').set_properties({ "range" : [-45, 45], "unit" : "degrees", "default_value" : -45, "title" : "disturbance amplitude" })     * dy.float64(math.pi / 180.0)
sample_disturbance     = dy.convert(dy.system_input( baseDatatype ).set_name('sample_disturbance').set_properties({ "range" : [0, 300], "unit" : "samples", "default_value" : 0, "title" : "time of disturbance" }), target_type=dy.DataTypeInt32(1) )

# parameters
wheelbase = 3.0

# create storage for the reference path:
# distance on path (D), position (X/Y), path orientation (PSI), curvature (K)
path = {}
path['D'] = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['D'] )
path['X'] = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['X'] )
path['Y'] = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['Y'] )
path['PSI'] = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['PSI'] )
path['K'] = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['K'] )

path['samples'] = example_data.Nmax

# create placeholders for the plant output signals
x   = dy.signal()
y   = dy.signal()
psi = dy.signal()

# track the evolution of the closest point on the path to the vehicles position
tracked_index, Delta_index, closest_distance = tracker(path, x, y)

# get the reference
x_r, y_r, psi_r = sample_path(path, index=tracked_index )

# add sign information to the distance
Delta_l = distance_to_Delta_l( closest_distance, psi_r, x_r, y_r, x, y )

# feedback control
Delta_u = dy.PID_controller(r=dy.float64(0.0), y=Delta_l, Ts=0.01, kp=k_p, ki = dy.float64(0.0), kd = dy.float64(0.0)) # 

# path tracking
steering = psi_r - psi + Delta_u
steering = dy.unwrap_angle(angle=steering, normalize_around_zero = True) 

#
# The model of the vehicle including a disturbance
#

# model the disturbance
disturbance_transient = np.concatenate(( cosra(50, 0, 1.0), co(10, 1.0), cosra(50, 1.0, 0) ))
steering_disturbance, i = dy.play(disturbance_transient, start_trigger=dy.counter() == sample_disturbance, auto_start=False)

# apply disturbance to the steering input
disturbed_steering = steering + steering_disturbance * disturbance_amplitude

# steering angle limit
disturbed_steering = dy.saturate(u=disturbed_steering, lower_limit=-math.pi/2.0, uppper_limit=math.pi/2.0)

# the model of the vehicle
x_, y_, psi_ = discrete_time_bicycle_model(disturbed_steering, velocity, wheelbase)

# close the feedback loops
x << x_
y << y_
psi << psi_

# main simulation ouput
dy.set_primary_outputs([ x, y, x_r, y_r, psi, psi_r, steering, Delta_l, steering_disturbance, disturbed_steering, tracked_index, Delta_index], 
        ['x', 'y', 'x_r', 'y_r', 'psi', 'psi_r', 'steering', 'Delta_l', 'steering_disturbance', 'disturbed_steering', 'tracked_index', 'Delta_index'])

# generate code
sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(enable_tracing=False), folder="generated/", build=True)

#
dy.clear()
