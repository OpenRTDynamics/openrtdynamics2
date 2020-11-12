import openrtdynamics2.lang as dy

import os
# 
import math
import numpy as np

from vehicle_lib.vehicle_lib import *
import vehicle_lib.example_data as example_data

# cfg
advanced_control = True

#
# A vehicle controlled to follow a given path 
#

system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 

# define simulation inputs
velocity       = dy.system_input( baseDatatype ).set_name('velocity').set_properties({ "range" : [0, 50], "unit" : "m/s", "default_value" : 23.75, "title" : "vehicle velocity" })
k_p            = dy.system_input( baseDatatype ).set_name('k_p').set_properties({ "range" : [0, 4.0], "default_value" : 0*0.112, "title" : "controller gain" })

disturbance_amplitude  = dy.system_input( baseDatatype ).set_name('disturbance_amplitude').set_properties({ "range" : [-45, 45], "unit" : "degrees", "default_value" : 0, "title" : "disturbance amplitude" })     * dy.float64(math.pi / 180.0)
sample_disturbance     = dy.convert(dy.system_input( baseDatatype ).set_name('sample_disturbance').set_properties({ "range" : [0, 300], "unit" : "samples", "default_value" : 0, "title" : "time of disturbance" }), target_type=dy.DataTypeInt32(1) )


distance_ahead   = dy.system_input( baseDatatype ).set_name('distance_ahead').set_properties({ "range" : [0, 20.0], "default_value" : 5.0, "title" : "distance ahead" })

if advanced_control:

    z_inf            = dy.system_input( baseDatatype ).set_name('z_inf').set_properties({ "range" : [0, 1.0], "default_value" : 0.981, "title" : "z_inf" })
    lateral_gain     = dy.system_input( baseDatatype ).set_name('lateral_gain').set_properties({ "range" : [-4000.0, 4000.0], "default_value" : 5.0, "title" : "lateral_gain" })

# parameters
wheelbase = 3.0

# create storage for the reference path:
# distance on path (D), position (X/Y), path orientation (PSI), curvature (K)
path = {}
path['D']   = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['D'] )
path['X']   = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['X'] )
path['Y']   = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['Y'] )
path['PSI'] = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['PSI'] )
path['K']   = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=example_data.output['K'] )

path['samples'] = example_data.Nmax

# create placeholders for the plant output signals
x   = dy.signal()
y   = dy.signal()
psi = dy.signal()

# track the evolution of the closest point on the path to the vehicles position
tracked_index, Delta_index, closest_distance = tracker(path, x, y)

#if advanced_control:
Delta_index_ahead, distance_residual, Delta_index_ahead_i1 = tracker_distance_ahead(path, current_index=tracked_index, distance_ahead=distance_ahead)


# get the reference
x_r, y_r, psi_r, K_r = sample_path(path, index=tracked_index )


x_r_km1, y_r_km1, psi_r_km1, K_r_km1 = sample_path(path, index=tracked_index - dy.int32(-1) )
x_r_kp1, y_r_kp1, psi_r_kp1, K_r_kp1 = sample_path(path, index=tracked_index - dy.int32( 1) )

distance_km1 = distance_between( x_r_km1, y_r_km1, x, y )
distance_kp1 = distance_between( x_r_kp1, y_r_kp1, x, y )

# x_r, y_r, psi_r = sample_path_finite_difference(path, index=tracked_index )



if advanced_control:
    x_r_ahead, y_r_ahead, psi_r_ahead, K_r_ahead = sample_path(path, index=tracked_index + Delta_index_ahead )

# add sign information to the distance
Delta_l = distance_to_Delta_l( closest_distance, psi_r, x_r, y_r, x, y )

# reference for the lateral distance


if advanced_control:

    #Delta_l_r = z_tf( K_r_ahead, z * (1-0.9) / (z-0.9) ) # * dy.float64( 0.1 )
    #Delta_l_r = dy.diff( dy.dtf_lowpass_1_order( dy.dtf_lowpass_1_order(K_r_ahead, 0.97), 0.97 ) ) * dy.float64( -700.0 )

    Delta_l_r_1 = dy.diff( dy.dtf_lowpass_1_order( dy.dtf_lowpass_1_order(K_r, z_inf), z_inf ) ) * lateral_gain * dy.float64( -1.0 )
    Delta_l_r_2 = dy.diff( dy.dtf_lowpass_1_order( dy.dtf_lowpass_1_order(K_r_ahead, z_inf), z_inf ) ) * lateral_gain # dy.float64( -700.0 )

    Delta_l_r = Delta_l_r_1 + Delta_l_r_2 

else:
    Delta_l_r = dy.float64(0.0)



# feedback control
Delta_u = dy.PID_controller(r=Delta_l_r, y=Delta_l, Ts=0.01, kp=k_p, ki = dy.float64(0.0), kd = dy.float64(0.0)) # 

# path tracking
steering = psi_r - psi + Delta_u
#steering = psi_r_ahead - psi + Delta_u
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
if advanced_control:

    dy.set_primary_outputs([ x, y, x_r, y_r, psi, psi_r, steering, Delta_l, distance_km1, distance_kp1, steering_disturbance, disturbed_steering, tracked_index, Delta_index, Delta_index_ahead, distance_residual, Delta_index_ahead_i1, K_r_ahead, Delta_l_r], 
            ['x', 'y', 'x_r', 'y_r', 'psi', 'psi_r', 'steering', 'Delta_l', 'distance_km1', 'distance_kp1', 'steering_disturbance', 'disturbed_steering', 'tracked_index', 'Delta_index', 'Delta_index_ahead', 'distance_residual', 'Delta_index_ahead_i1', 'K_r_ahead', 'Delta_l_r'])

# generate code
sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(enable_tracing=False), folder="generated/", build=True)

#
dy.clear()
