import math
import numpy as np
import openrtdynamics2.lang as dy

# nice functions to create paths
def co(time, val, Ts=1.0):
    return val * np.ones(int(math.ceil(time / Ts)))


def cosra(time, val1, val2, Ts=1.0):
    N = int(math.ceil(time / Ts))
    return val1 + (val2-val1) * (0.5 + 0.5 * np.sin(math.pi * np.linspace(0, 1, N) - math.pi/2))


def ra(time, val1, val2, Ts=1.0):
    N = int(math.ceil(time / Ts))
    return np.linspace(val1, val2, N)




def discrete_time_bicycle_model(delta, v, wheelbase):
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



def distance_between( x1, y1, x2, y2 ):

    dx_ = x1 - x2
    dy_ = y1 - y2

    return dy.sqrt(  dx_*dx_ + dy_*dy_ )


def tracker(path, x, y):
    index_track   = dy.signal()

    with dy.sub_loop( max_iterations=1000 ) as system:

        search_index_increment = dy.int32(1) # positive increment assuming positive velocity

        Delta_index = dy.sum(search_index_increment, initial_state=-1 )
        Delta_index_previous_step = Delta_index - search_index_increment

        x_test = dy.memory_read( memory=path['X'], index=index_track + Delta_index ) 
        y_test = dy.memory_read( memory=path['Y'], index=index_track + Delta_index )

        distance = distance_between( x_test, y_test, x, y )

        distance_previous_step = dy.delay(distance, initial_state=100000)
        minimal_distance_reached = distance_previous_step < distance

        # introduce signal names
        distance.set_name('tracker_distance')
        minimal_distance_reached.set_name('minimal_distance_reached')

        # break condition
        system.loop_until( minimal_distance_reached )

        # return        
        system.set_outputs([ Delta_index_previous_step, distance_previous_step ])


    Delta_index = system.outputs[0].set_name('tracker_Delta_index')
    distance = system.outputs[1].set_name('distance')

    index_track_next = index_track + Delta_index 

    index_track << dy.delay(index_track_next, initial_state=1)

    return index_track, Delta_index, distance


def tracker_distance_ahead(path, current_index, distance_ahead):
    """

                  <----- Delta_index_track ----->
        array: X  X  X  X  X  X  X  X  X  X  X  X  X  X  X 
                  ^               
            current_index
    """

    if 'Delta_d' in path:
        # constant sampling interval in distance
        # computation can be simplified
        pass


    def J( index ):

        d_test = dy.memory_read( memory=path['D'], index=index ) 
        distance = dy.abs( d_test - dy.float64(distance_ahead) )

        return distance
    

    Delta_index_track   = dy.signal()

    # initialize J_star
    J_star_0 = J(current_index + Delta_index_track)

    #
    # compute the direction in which J has its decent
    # if true: with increasing index J increases  --> decrease search index
    # if false: with increasing index J decreases --> increase search index
    #
    direction_flag = J(current_index + Delta_index_track + dy.int32(1)) > J_star_0

    search_index_increment = dy.int32(1) 
    search_index_increment = dy.conditional_overwrite(search_index_increment, direction_flag, dy.int32(-1) )

    # loop to find the minimum of J
    with dy.sub_loop( max_iterations=1000 ) as system:


        # J_star(k) - the smallest J found so far
        J_star = dy.signal()
        # J_star.inherit_datatype(J_star_0)

        # inc- / decrease the search index
        Delta_index = dy.sum(search_index_increment, initial_state=0 )

        # sample the cost function and check if it got smaller in this step
        J_to_verify = J( current_index + Delta_index_track + Delta_index )
        step_caused_improvment = J_to_verify < J_star

        # replace the 
        J_star_next = dy.conditional_overwrite( J_star, step_caused_improvment, J_to_verify )

        # state for J_star
        J_star << dy.delay( J_star_next, initial_state=J_star_0 )


        # loop break condition
        system.loop_until( dy.logic_not( step_caused_improvment ) )

        # return the results computed in the loop        
        system.set_outputs([ Delta_index ])



    Delta_index_track_next = Delta_index_track + system.outputs[0]
    Delta_index_track << dy.delay(Delta_index_track_next, initial_state=0)


    return Delta_index_track



def global_lookup_distance_index( path_distance_storage, path_x_storage, path_y_storage, distance ):
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




def sample_path(path, index):

    y_r = dy.memory_read( memory=path['Y'], index=index ) 
    x_r = dy.memory_read( memory=path['X'], index=index ) 
    psi_r = dy.memory_read( memory=path['PSI'], index=index ) 

    return x_r, y_r, psi_r


def distance_to_Delta_l( distance, psi_r, x_r, y_r, x, y ):

    psi_tmp = dy.atan2(y - y_r, x - x_r)
    delta_angle = dy.unwrap_angle( psi_r - psi_tmp, normalize_around_zero=True )
    sign = dy.conditional_overwrite(dy.float64(1.0), delta_angle > dy.float64(0) ,  -1.0  )
    Delta_l = distance * sign

    return Delta_l




