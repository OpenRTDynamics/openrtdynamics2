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

        index_increment = dy.int32(1) # positive increment assuming positive velocity

        Delta_index = dy.sum(index_increment, initial_state=-1 )
        Delta_index_previous_step = Delta_index - index_increment

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


def lookup_closest_point( N, path_distance_storage, path_x_storage, path_y_storage, x, y ):
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
        distance      = min_distance_to_path;

    """
    array_type = dy.DataTypeArray( N, datatype=dy.DataTypeFloat64(1) )
    outputs = dy.generic_cpp_static(input_signals=[ path_distance_storage, path_x_storage, path_y_storage, x, y ], 
                                    input_names=[ 'path_distance_storage', 'path_x_storage', 'path_y_storage', 'x_', 'y_' ], 
                                    input_types=[ array_type, array_type, array_type, dy.DataTypeFloat64(1), dy.DataTypeFloat64(1) ], 
                                    output_names=[ 'index_closest', 'index_start', 'distance'],
                                    output_types=[ dy.DataTypeInt32(1), dy.DataTypeInt32(1), dy.DataTypeFloat64(1) ],
                                    cpp_source_code = source_code )

    index_start = outputs[0]
    index_closest = outputs[1]
    distance     = outputs[2]

    return index_closest, distance, index_start



# def sample_path(path_distance_storage, path_x_storage, path_y_storage, index):

#     y1 = dy.memory_read( memory=path_y_storage, index=index ) 
#     y2 = dy.memory_read( memory=path_y_storage, index=index + dy.int32(1) )

#     x1 = dy.memory_read( memory=path_x_storage, index=index ) 
#     x2 = dy.memory_read( memory=path_x_storage, index=index + dy.int32(1) )

#     Delta_x = x2 - x1
#     Delta_y = y2 - y1

#     psi_r = dy.atan2(Delta_y, Delta_x)
#     x_r = x1
#     y_r = y1

#     return x_r, y_r, psi_r

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




