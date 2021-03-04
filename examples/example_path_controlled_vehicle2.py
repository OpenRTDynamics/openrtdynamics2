import openrtdynamics2.lang as dy
from openrtdynamics2.dsp import *

import os
import json 
import math
import numpy as np

from vehicle_lib.vehicle_lib import *
#import vehicle_lib.example_data as example_data

# load track data
with open("track_data/simple_track.json", "r") as read_file:
    track_data = json.load(read_file)

# cfg
advanced_control = False

#
# A vehicle controlled to follow a given path 
#

system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 

# define simulation inputs
if not advanced_control:


    velocity               = dy.system_input( dy.DataTypeFloat64(1), name='velocity',              default_value=7.2,   value_range=[0, 25],   title="vehicle velocity")
    k_p                    = dy.system_input( dy.DataTypeFloat64(1), name='k_p',                   default_value=0.612, value_range=[0, 4.0],  title="controller gain")
    disturbance_amplitude  = dy.system_input( dy.DataTypeFloat64(1), name='disturbance_amplitude', default_value=-11.0, value_range=[-45, 45], title="disturbance amplitude") * dy.float64(math.pi / 180.0)
    sample_disturbance     = dy.system_input( dy.DataTypeInt32(1),   name='sample_disturbance',    default_value=50,    value_range=[0, 300],  title="disturbance position")
    z_inf_compensator      = dy.system_input( dy.DataTypeFloat64(1), name='z_inf',                 default_value=0.9,   value_range=[0, 1.0],  title="z_inf_compensator")





if advanced_control:
    velocity       = dy.system_input( baseDatatype ).set_name('velocity').set_properties({ "range" : [0, 25], "unit" : "m/s", "default_value" : 23.75, "title" : "vehicle velocity" })
    k_p            = dy.system_input( baseDatatype ).set_name('k_p').set_properties({ "range" : [0, 4.0], "default_value" : 0.24, "title" : "controller gain" })

    disturbance_amplitude  = dy.system_input( baseDatatype ).set_name('disturbance_amplitude').set_properties({ "range" : [-45, 45], "unit" : "degrees", "default_value" : 0, "title" : "disturbance amplitude" })     * dy.float64(math.pi / 180.0)
    sample_disturbance     = dy.convert(dy.system_input( baseDatatype ).set_name('sample_disturbance').set_properties({ "range" : [0, 300], "unit" : "samples", "default_value" : 0, "title" : "disturbance position" }), target_type=dy.DataTypeInt32(1) )

    distance_ahead   = dy.system_input( baseDatatype ).set_name('distance_ahead').set_properties({ "range" : [0, 20.0], "default_value" : 5.0, "title" : "distance ahead" })
    z_inf            = dy.system_input( baseDatatype ).set_name('z_inf').set_properties({ "range" : [0, 1.0], "default_value" : 0.981, "title" : "z_inf" })
    lateral_gain     = dy.system_input( baseDatatype ).set_name('lateral_gain').set_properties({ "range" : [-4000.0, 4000.0], "default_value" : 5.0, "title" : "lateral_gain" })

    z_inf_compensator      = dy.system_input( baseDatatype ).set_name('z_inf_compensator').set_properties({ "range" : [0, 1.0], "default_value" : 0.9, "title" : "z_inf_compensator" })


# parameters
wheelbase = 3.0
Ts=0.01

# driving with constant velocity
v_dot=dy.float64(0)


# create storage for the reference path:
path = import_path_data(track_data)



# create placeholders for the plant output signals
x       = dy.signal()
y       = dy.signal()
psi     = dy.signal()
psi_dot = dy.signal()
delta   = dy.signal()
a_lat   = dy.signal()

# track the evolution of the closest point on the path to the vehicles position
tracked_index, Delta_index, closest_distance = tracker(path, x, y)

second_closest_distance, index_second_star = find_second_closest( path, x, y, index_star=tracked_index )
interpolated_closest_distance = compute_distance_from_linear_interpolation( second_closest_distance, closest_distance  )

dy.append_primay_ouput(interpolated_closest_distance, 'interpolated_closest_distance')
dy.append_primay_ouput(second_closest_distance, 'second_closest_distance')

if advanced_control:
    Delta_index_ahead, distance_residual, Delta_index_ahead_i1 = tracker_distance_ahead(path, current_index=tracked_index, distance_ahead=distance_ahead)

    dy.append_primay_ouput(distance_residual, 'distance_residual')
    dy.append_primay_ouput(Delta_index_ahead_i1, 'Delta_index_ahead_i1')
    dy.append_primay_ouput(Delta_index_ahead, 'Delta_index_ahead')

# verify
if False:
    index_closest_compare, distance_compare, index_start_compare = lookup_closest_point( N=path['samples'], path_distance_storage=path['D'], path_x_storage=path['X'], path_y_storage=path['Y'], x=x, y=y )
    dy.append_primay_ouput(index_closest_compare, 'index_closest_compare')


# get the reference
x_r, y_r, psi_rr, K_r = sample_path(path, index=tracked_index + dy.int32(1) )  # new sampling
# x_r, y_r, psi_rr = sample_path_finite_difference(path, index=tracked_index ) # old sampling





# compute the noise-reduced path orientation Psi_r from curvature
#
# NOTE: velocity: should be the projection of the vehicle velocity on the path?
#
psi_r, psi_r_dot = compute_path_orientation_from_curvature( Ts, velocity, psi_rr, K_r, L=1.0 ) 

dy.append_primay_ouput(psi_rr,     'psi_rr')
dy.append_primay_ouput(psi_r_dot, 'psi_r_dot')

#
# verify the data
#
if False:
    x_r_km1, y_r_km1, psi_r_km1, K_r_km1 = sample_path(path, index=tracked_index - dy.int32(-1) )
    x_r_kp1, y_r_kp1, psi_r_kp1, K_r_kp1 = sample_path(path, index=tracked_index - dy.int32( 1) )

    distance_km1 = distance_between( x_r_km1, y_r_km1, x, y )
    distance_kp1 = distance_between( x_r_kp1, y_r_kp1, x, y )

    dy.append_primay_ouput(distance_km1, 'distance_km1')
    dy.append_primay_ouput(distance_kp1, 'distance_kp1')


if advanced_control:
    x_r_ahead, y_r_ahead, psi_r_ahead, K_r_ahead = sample_path(path, index=tracked_index + Delta_index_ahead )

    dy.append_primay_ouput(K_r_ahead, 'K_r_ahead')

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

dy.append_primay_ouput(Delta_l_r, 'Delta_l_r')


# feedback control
Delta_l_filt = dy.dtf_lowpass_1_order( dy.dtf_lowpass_1_order(Delta_l, z_inf_compensator), z_inf_compensator )
u = dy.PID_controller(r=Delta_l_r, y=Delta_l_filt, Ts=Ts, kp=k_p, ki = dy.float64(0.0), kd = dy.float64(0.0)) # 

dy.append_primay_ouput(Delta_l_filt, 'Delta_l_filt')

# model of lateral distance
z_inf_compensator_ = 0.9

# L_Delta_l = 0.24 * Ts/(z-1) * ((1 - z_inf_compensator_) / (z - z_inf_compensator_)) * ((1 - z_inf_compensator_) / (z - z_inf_compensator_))
# T_Delta_l = L_Delta_l / ( 1 + L_Delta_l )
# Delta_l_model = z_tf( Delta_l_r, T_Delta_l ) # * dy.float64( 0.1 )



L_Delta_l = Ts/(z-1) 

Delta_l_model = z_tf( u, L_Delta_l )




dy.append_primay_ouput(Delta_l_model, 'Delta_l_model')


# path tracking
# resulting lateral model u --> Delta_l : 1/s
Delta_u = dy.asin( dy.saturate(u / velocity, -0.99, 0.99) )
steering =  psi_r - psi + Delta_u
steering = dy.unwrap_angle(angle=steering, normalize_around_zero = True)

dy.append_primay_ouput(Delta_u, 'Delta_u')
dy.append_primay_ouput(u, 'l_dot_r')


#
# safety function
#
# velocity: should be the projection of the vehicle velocity on the path?



# compute nominal steering and steering angle from curvature
delta_from_K, delta_dot_from_K, psi_dot_from_K = compute_nominal_steering_from_curvature( Ts=Ts, l_r=wheelbase, v=velocity, K_r=K_r )

dy.append_primay_ouput( delta_from_K,     'delta_from_K'     )
dy.append_primay_ouput( delta_dot_from_K, 'delta_dot_from_K' )

# compute nominal steering and carbody orientation from path heading
delta_from_heading, psi_from_heading, psi_dot_from_heading = compute_nominal_steering_from_path_heading( Ts=Ts, l_r=wheelbase, v=velocity, psi_r=psi_r )

dy.append_primay_ouput( delta_from_heading, 'delta_from_heading' )
dy.append_primay_ouput( psi_from_heading,   'psi_from_heading' )

# compute the nominal acceleration and the boundaries for the steering rate
a_lat_nominal, a_long_nominal = compute_accelearation( velocity, v_dot, delta=delta_from_K, delta_dot=delta_dot_from_K, psi_dot=psi_dot_from_K )

a_lat_min = a_lat_nominal - dy.float64(1.5)
a_lat_max = a_lat_nominal + dy.float64(1.5)

dy.append_primay_ouput( a_lat_nominal,   'a_lat_nominal' )

dy.append_primay_ouput( a_lat_min,   'a_lat_min' )
dy.append_primay_ouput( a_lat_max,   'a_lat_max' )

# compute boundaries for the steering command to ensure constraints on lateral acceleration and velocity
# Question: for delta and psi_dot use the nominal (psi_dot_from_K, delta_from_K) or measured (psi_dot, delta)

# delta_min, delta_max, delta_dot_min, delta_dot_max = compute_steering_constraints( velocity, v_dot, psi_dot=psi_dot, delta=delta, a_l_min=a_lat_min, a_l_max=a_lat_max )
delta_min, delta_max, delta_dot_min, delta_dot_max = compute_steering_constraints( velocity, v_dot, psi_dot=psi_dot_from_K, delta=delta_from_K, a_l_min=a_lat_min, a_l_max=a_lat_max )


dy.append_primay_ouput( delta_dot_min,   'delta_dot_min' )
dy.append_primay_ouput( delta_dot_max,   'delta_dot_max' )

# estimate steering rate of the real vehicle
# delta_dot_hat = dy.dtf_lowpass_1_order( dy.diff( steering, initial_state=steering ) / dy.float64(Ts), 0.1)
# dy.append_primay_ouput( delta_dot_hat,   'delta_dot_hat' )

delta_dot_hat_nosat = dy.diff( steering, initial_state=steering ) / dy.float64(Ts)
dy.append_primay_ouput( delta_dot_hat_nosat,   'delta_dot_hat_nosat' )

#
# apply saturation to the steering control variable
#

steering = dy.saturate(steering, delta_min, delta_max)
steering = dy.rate_limit( steering, Ts, delta_dot_min, delta_dot_max, initial_state=steering )

delta_dot_hat = dy.diff( steering, initial_state=steering ) / dy.float64(Ts)
dy.append_primay_ouput( delta_dot_hat,   'delta_dot_hat' )


#
# The model of the vehicle including a disturbance
#

# model the disturbance
disturbance_transient = np.concatenate(( cosra(50, 0, 1.0), co(10, 1.0), cosra(50, 1.0, 0) ))

steering_disturbance, _ = dy.play(disturbance_transient, start_trigger=dy.counter() == sample_disturbance, auto_start=False)
steering_disturbance = steering_disturbance * disturbance_amplitude

# # apply disturbance to the steering input
# disturbed_steering = steering + steering_disturbance * disturbance_amplitude

# # steering angle limit (model-intern)
# disturbed_steering = dy.saturate(u=disturbed_steering, lower_limit=-math.pi/2.0, upper_limit=math.pi/2.0)

# the model of the vehicle
# x_, y_, psi_, x_dot, y_dot, psi_dot = discrete_time_bicycle_model(disturbed_steering, velocity, Ts, wheelbase)

x_, y_, psi_, delta_, _delta_dot, a_lat_, _a_long, _x_dot, _y_dot, psi_dot_ = lateral_vehicle_model(steering, velocity, v_dot, Ts, wheelbase, delta_disturbance=steering_disturbance)


# close the feedback loops
x       << x_
y       << y_
psi     << psi_
psi_dot << psi_dot_
delta   << delta_
a_lat   << a_lat_





dy.append_primay_ouput(x, 'x')
dy.append_primay_ouput(y, 'y')
dy.append_primay_ouput(psi, 'psi')

dy.append_primay_ouput(steering, 'steering')

dy.append_primay_ouput(x_r, 'x_r')
dy.append_primay_ouput(y_r, 'y_r')
dy.append_primay_ouput(psi_r, 'psi_r')

dy.append_primay_ouput(Delta_l, 'Delta_l')

dy.append_primay_ouput(steering_disturbance, 'steering_disturbance')
# dy.append_primay_ouput(disturbed_steering, 'disturbed_steering')
dy.append_primay_ouput(tracked_index, 'tracked_index')
dy.append_primay_ouput(Delta_index, 'Delta_index')




# main simulation ouput
# if advanced_control:
#     dy.set_primary_outputs([ x, y, x_r, y_r, psi, psi_r, steering, Delta_l, distance_km1, distance_kp1, steering_disturbance, disturbed_steering, tracked_index, Delta_index, Delta_index_ahead, distance_residual, Delta_index_ahead_i1, K_r_ahead, Delta_l_r], 
#             ['x', 'y', 'x_r', 'y_r', 'psi', 'psi_r', 'steering', 'Delta_l', 'distance_km1', 'distance_kp1', 'steering_disturbance', 'disturbed_steering', 'tracked_index', 'Delta_index', 'Delta_index_ahead', 'distance_residual', 'Delta_index_ahead_i1', 'K_r_ahead', 'Delta_l_r'])

# generate code
sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(enable_tracing=False), folder="html/build/", build=True)

#
dy.clear()
