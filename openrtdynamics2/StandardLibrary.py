import math

from typing import Dict, List
from . import lang as dy
import numpy as np

def int32(value : int):
    return dy.const(value, dy.DataTypeInt32(1) )

def float64(value : float):
    return dy.const(value, dy.DataTypeFloat64(1) )

def boolean(value : int):
    return dy.const(value, dy.DataTypeBoolean(1) )




class Counter():
    """
        This class is meant to store the counter output signal as it might be used
        by more than one destination block. The instance of this class is per simulation
        and will be stored in the components property of the current get_simulation_context()
    """
    def __init__(self, counter_signal : dy.Signal):
        self.counter_signal_ = counter_signal
        self.hits = 0
    
    @property
    def output(self):
        self.hits += 1

        # print("counter cache hits ***: " + str(self.hits) )
        return self.counter_signal_



def counter():
    """
        Basic counter

        The integer output is increasing with each sampling instant by 1.
    """

    if not 'counter' in dy.get_simulation_context().components:
        # no counter has been defined in this system so far. Hence, create one.

        increase = dy.const(1, dy.DataTypeInt32(1) )
        cnt = dy.signal()
        tmp = dy.delay(cnt + increase)
        cnt << tmp 

        tmp.set_name('shared_couter')

        # store the output signal of the counter as it might be used again. 
        dy.get_simulation_context().components['counter'] = Counter(tmp)

    else:
        # use the output of an already created counter
        tmp = dy.get_simulation_context().components['counter'].output

    return tmp

def signal_sinus(N_period : int = 100, phi = None):
    """
        Signal generator for sinosoidal signals

        The output is computed as follows:

        y = sin( 1 / N_period * 2 * pi) + phi )

        N_period - period in sampling instants (type: constant integer)
        phi      - phase shift (signal)
    """

    if N_period <= 0:
        raise BaseException('N_period <= 0')

    if phi is None:
        phi = dy.float64(0.0)

    i = dy.counter_limited( upper_limit=N_period-1, reset_on_limit=True )
    y = dy.sin( i * dy.float64(1/N_period * 2*math.pi) + phi )

    return y

def signal_step(k_step : int):
    """
        Signal generator for a step signal

        k_step - the sampling index as returned by counter() at which the step appears.
    """
    k = dy.counter()
    y = dy.int32(k_step) <= k

    return y

def signal_ramp(k_start : int):
    """
        Signal generator for a ramp signal

        k_start - the sampling index as returned by counter() at which the ramp starts increasing.
    """
    # TODO
    k = dy.counter()
    active = dy.int32(k_start) <= k

    linearRise = dy.convert( (k - dy.int32(k_start) ), dy.DataTypeFloat64(1) )
    activation = dy.convert( active, dy.DataTypeFloat64(1) )

    return activation * linearRise



def dtf_lowpass_1_order(u : dy.Signal, z_infinity : float):

    zinf = dy.float64( z_infinity )
    zinf_ = dy.float64( 1 - z_infinity )

    y_delayed = dy.signal()
    y =  zinf * y_delayed + zinf_ * u

    y_delayed << dy.delay(y)
    
    return y



def dtf_filter(u : dy.Signal, num_coeff : List[float], den_coeff : List[float] ):

    """
    Discrete time transfer function

    This filter realizes a discrete-time transfer function by using 'direct form II'
    c.f. https://en.wikipedia.org/wiki/Digital_filter .

            b0 + b1 z^-1 + b2 z^-2 + ... + bN z^-N
    H(z) = ----------------------------------------
             1 + a1 z^-1 + a2 z^-2 + ... + aM z^-M

    The coefficient vectors num_coeff and den_coeff describe the numerator and 
    denominator polynomials, respectively, and are defined as follows:

    num_coeff = [b0, b1, .., bN]
    den_coeff = [a1, a2, ... aM] .
    
    """


    # get filter order
    N = len(num_coeff)-1

    # feedback start signal
    z_pre = dy.signal()

    # array to store state signals
    z_ = []

    # create delay chain
    z_iterate = z_pre
    for i in range(0,N):

        z_iterate = dy.delay( z_iterate ).extendName('_z' + str(i) )
        z_.append( z_iterate ) 


    # build feedback path
    #
    # a1 = den_coeff[0]
    # a2 = den_coeff[1]
    # a3 = den_coeff[2]
    #        ...
    sum_feedback = u
    for i in range(0,N):

        a_ip1 = dy.float64( den_coeff[i] ).extendName('_a' + str(i+1) )

        sum_feedback = sum_feedback - a_ip1 * z_[i]

    sum_feedback.extendName('_i')


    # close the feedback loop
    z_pre << sum_feedback

    # build output path
    #
    # b0 = num_coeff[0]
    # b1 = num_coeff[1]
    # b2 = num_coeff[2]
    #        ...    
    for i in range(0,N+1):
        
        b_i = dy.float64( num_coeff[i] ).extendName('_b' + str(i) )

        if i==0:
            y = b_i * sum_feedback
        else:
            y = y + b_i * z_[i-1]

    # y is the filter output   
    return y





def diff(u : dy.Signal):
    """
        Discrete difference

        y = u[k] - u[k-1] 
    """

    i = dy.delay( u )
    y = dy.add( [ i, u ], [ -1, 1 ] )

    return y

def sum(u : dy.Signal):
    """
        Accumulative sum

        y[k+1] = y[k] + u[k]
    """

    y = dy.signal()    
    y << dy.delay(y + u)

    return y

def euler_integrator( u : dy.Signal, sampling_rate : float, initial_state = 0.0):
    """
        Euler (forward) integrator

        y[k+1] = y[k] + sampling_rate * u[k]
    """

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, sampling_rate ] )
    y = dy.delay( i, initial_state )

    yFb << y

    return y
    

def counter_limited( upper_limit, stepwidth=None, initial_state = 0, reset=None, reset_on_limit=False ):
    
    if stepwidth is None:
        stepwidth = dy.int32(1)

    counter = dy.signal()
    reached_upper_limit = counter >= dy.int32(upper_limit)

    # increase the counter until the end is reached
    new_counter = counter + dy.conditional_overwrite(stepwidth, reached_upper_limit, 0)

    if reset is not None:
        # reset in case this is requested
        new_counter = dy.conditional_overwrite(new_counter, reset, 0)

    if reset_on_limit:
        new_counter = dy.conditional_overwrite(new_counter, reached_upper_limit, 0)

    # introduce a state variable for the counter
    counter << dy.delay( new_counter, initial_state=initial_state )

    return counter



def play( sequence_array, reset, reset_on_end=False ):
    sequence_array_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=sequence_array )



    playback_index = counter_limited( upper_limit=np.size(sequence_array), stepwidth=dy.int32(1), initial_state=np.size(sequence_array), reset=reset, reset_on_limit=reset_on_end)



    # subsampling = dy.int32(1)
    # playback_index = dy.signal()
    # reached_end = playback_index == dy.int32(np.size(sequence_array))

    # # increase the index counter until the end is reached
    # new_index = playback_index + dy.conditional_overwrite(subsampling, reached_end , 0)

    # # reset
    # new_index = dy.conditional_overwrite(new_index, reset, 0)

    # # introduce a state variable for the counter
    # playback_index << dy.delay( new_index, initial_state=np.size(sequence_array) )







    # sample the given data
    output = dy.memory_read(sequence_array_storage, playback_index)

    return output, playback_index


def PID_controller(r, y, Ts, kp, ki = None, kd = None):
    Ts = dy.float64(Ts)

    # control error
    e = r - y

    # P
    u = kp * e

    # D
    if kd is not None:
        u = u + dy.diff(e) * kd / Ts

    # I
    if ki is not None:
        u = u + dy.sum(e) * ki * Ts

    return u
