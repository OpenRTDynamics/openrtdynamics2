import math

from typing import Dict, List
from . import lang as dy
import numpy as np

from .block_prototypes import *

#
# constants
#

def int32(value):
    """
        cast anything to DataTypeInt32
    """

    if isinstance(  value, dy.SignalUserTemplate ):
        # already a singal
        return value
    else:
        # create a new constant
        return dy.const(value, dy.DataTypeInt32(1) )

def float64(value):
    """
        cast anything to DataTypeFloat64
    """
    if isinstance(  value, dy.SignalUserTemplate ):
        # already a singal
        return value
    else:
        # create a new constant
        return dy.const(value, dy.DataTypeFloat64(1) )


def boolean(value : int):
    """
        cast anything to DataTypeBoolean
    """
    if isinstance(  value, dy.SignalUserTemplate ):
        # already a singal
        return value
    else:
        # create a new constant
        return dy.const(value, dy.DataTypeBoolean(1) )



#
#
#

def initial_event():
    """
        Fires an event of the first time instant after the reset of the system
    """

    # TODO: introduce caching like done for counter()

    return dy.counter() == int32(0)


#
# Delay - the basis for all dynamic elements
#
def delay(u , initial_state = None):
    """
        unit delay

        delay the input u by one sampling instant

        y[k+1] = u[k], y[0] = initial_state

        u             - the input signal to delay
        initial_state - the initial state (signal or constant value)
    """

    if not isinstance( initial_state, dy.SignalUserTemplate ):
        return dy.delay__( u, initial_state )

    else:

        event_on_first_sample = initial_event()

        delayed_input = dy.delay__( u, None )
        delayed_input = dy.conditional_overwrite( delayed_input, event_on_first_sample, initial_state )

        return delayed_input

def sample_and_hold(u, event, initial_state = None):
    """
        sample & hold

        Samples the input when event is true and hold this value for the proceeding time instants. 

        u             - the input
        event         - the trigger signal to perform the sampling
        initial_state - the initial output

        return values

        the sampled input

    """

    # NOTE: this could be implemented in a more comp. efficient way directly in C in block_prototypes.py

    y = dy.signal()

    delayed_y = delay( y, initial_state )
    y << dy.conditional_overwrite( delayed_y, event, u )

    return y

#
# static functions
#

def unwrap_angle(angle, normalize_around_zero = False):
    """
        Unwrap an angle

        Unrap and normalize the input angle to the range 

          1) [0, 2*pi[     in case normalize_around_zero == false
          2) [-pi, pi]     in case normalize_around_zero == true
    """

    def normalize_aruond_zero(angle):
        """
            Normalize an angle

            Normalize an angle to a range [-pi, pi]

            Important: the assumed range for the input is - 2*pi <= angle <= 2*p
        """

        tmp = angle            + dy.conditional_overwrite( dy.float64(0), angle <= float64(-math.pi), 2*math.pi )
        normalized_angle = tmp + dy.conditional_overwrite( dy.float64(0), angle > float64(math.pi), -2*math.pi )

        return normalized_angle

    #
    #
    angle_ = dy.fmod(angle, dy.float64(2*math.pi) )

    unwrapped_angle = angle_ + dy.conditional_overwrite( dy.float64(0), angle_ < float64(0), 2*math.pi )

    if normalize_around_zero:
        return normalize_aruond_zero(unwrapped_angle)
    else:
        return unwrapped_angle





def saturate(u, lower_limit = None, uppper_limit = None):
    """
        saturate the input signal

        The output is the saturated input

        lower_limit   - lower bound for the output 
        uppper_limit  - upper bound for the output
    """

    y = u

    if lower_limit is not None:
        y = dy.conditional_overwrite( y, y < float64(lower_limit), lower_limit )
    
    if uppper_limit is not None:
        y = dy.conditional_overwrite( y, y > float64(uppper_limit), uppper_limit )

    return y


def rate_limit( u, Ts, lower_limit, uppper_limit, initial_state = 0 ):
    """
        rate limiter

        Ts           - sampling time (constant)
        lower_limit  - lower rate limit
        upper_limit  - upper rate limit
    """

    Ts_ = float64(Ts)

    y = dy.signal()

    omega = u - y
    omega_sat = saturate(omega, float64(lower_limit) * Ts_, float64(uppper_limit) * Ts_)
    y << euler_integrator( omega_sat, 1, initial_state=initial_state)

    return y


# def rate_limit_2nd( u, Ts, lower_limit, uppper_limit, gain, initial_state = 0 ):

#     Ts_ = float64(Ts)

#     y = dy.signal()

#     e = ( u - y )
#     omega = dy.tan( u - y ) * dy.float64(gain)
#     omega_sat = saturate(omega, lower_limit * Ts_, uppper_limit * Ts_)

#     y << euler_integrator(  omega_sat, 1, initial_state=initial_state)

#     return y



#
# Counters
#

# TODO: mark as private
class __Counter():
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


#
# dynamic functions
#

def counter():
    """
        Basic counter

        The integer output is increasing with each sampling instant by 1.
        Counting starts at zero.
    """

    if not 'counter' in dy.get_simulation_context().components:
        # no counter has been defined in this system so far. Hence, create one.

        increase = dy.const(1, dy.DataTypeInt32(1) )
        cnt = dy.signal()
        tmp = dy.delay(cnt + increase)
        cnt << tmp 

        tmp.set_name('shared_couter')

        # store the output signal of the counter as it might be used again. 
        dy.get_simulation_context().components['counter'] = __Counter(tmp)

    else:
        # use the output of an already created counter
        tmp = dy.get_simulation_context().components['counter'].output

    return tmp





def counter_triggered( upper_limit, stepwidth=None, initial_state = 0, reset=None, reset_on_limit:bool=False, start_trigger=None, pause_trigger=None, auto_start:bool=True, no_delay:bool=False ):
    """
        A generic counter

        Features:
        .) upper limit
        .) triggerable start/pause
        .) resetable
        .) dynamic adjustable step-size

        upper_limit              - the upper limit of the counter
        initial_state            - the state after reset
        reset                    - reset the counter
        reset_on_limit           - reset counter once the upper limit is reached
        start_trigger            - event to start counting
        pause_trigger            - event to pause counting
        auto_start               - start counting automatically
        no_delay                 - when True the new value of the counter is returned without delay 
    """

    if stepwidth is None:
        stepwidth = dy.int32(1)

    counter = dy.signal()

    reached_upper_limit = counter > dy.int32(upper_limit)

    if start_trigger is None:
        start_trigger = dy.boolean(0)

    # 
    if pause_trigger is not None: 
        activate_trigger = dy.logic_or(reached_upper_limit, pause_trigger)
    else:
        if not auto_start:
            activate_trigger = reached_upper_limit
        else:
            # when auto_start is active, continue counting after reset on reached_upper_limit
            activate_trigger = dy.boolean(0)


    # state for pause/counting
    paused =  dy.flipflop(activate_trigger=activate_trigger, disable_trigger=start_trigger, initial_state = not auto_start).set_name('paused')

    # prevent counter increase
    stepwidth = dy.conditional_overwrite(stepwidth, paused, 0).set_name('stepwidth')

    # increase the counter until the end is reached
    new_counter = counter + dy.conditional_overwrite(stepwidth, reached_upper_limit, 0)

    if reset is not None:
        # reset in case this is requested
        new_counter = dy.conditional_overwrite(new_counter, reset, initial_state)

    if reset_on_limit:
        new_counter = dy.conditional_overwrite(new_counter, reached_upper_limit, initial_state)

    # introduce a state variable for the counter
    counter << dy.delay( new_counter, initial_state=initial_state )

    if not no_delay:
        return counter
    else:
        return new_counter


# def toggle(trigger, initial_state=False):

#     state = dy.signal()

#     state << dy.flipflop( dy.logic_and( dy.logic_not( state ), trigger ),  dy.logic_and( dy.logic_not( trigger ), state ), 
#                             initial_state=initial_state, 
#                             nodelay=False)

#     return state



def toggle(trigger, initial_state=False):

    state = dy.signal()

    activate   = dy.logic_and( dy.logic_not( state ), trigger )
    deactivate = dy.logic_and( trigger , state)

    tmp = dy.flipflop( activate, deactivate, 
                            initial_state = 0, 
                            nodelay=False )

    state << tmp

    return state, activate, deactivate
    
def signal_square(period, phase):

    trigger = signal_periodic_impulse(period, phase)

    state, activate, deactivate = toggle(trigger)

    return state, activate, deactivate

    #return trigger

#
# signal generators
#

def signal_sinus(N_period : int = 100, phi = None):
    """
        Signal generator for sinosoidal signals

        The output is computed as follows:

        y = sin( k * (1 / N_period * 2 * pi) + phi )

        k - is the sampling index

        N_period - period in sampling instants (type: constant integer)
        phi      - phase shift (signal)
    """

    if N_period <= 0:
        raise BaseException('N_period <= 0')

    if phi is None:
        phi = dy.float64(0.0)

    i = dy.counter_triggered( upper_limit=N_period-1, reset_on_limit=True )
    y = dy.sin( i * dy.float64(1/N_period * 2*math.pi) + phi )

    return y

def signal_step(k_step):
    """
        Signal generator for a step signal

        k_step - the sampling index as returned by counter() at which the step appears.
    """
    k = dy.counter()
    y = dy.int32(k_step) <= k

    return y

def signal_ramp(k_start):
    """
        Signal generator for a ramp signal

        k_start - the sampling index as returned by counter() at which the ramp starts increasing.
    """
    k = dy.counter()
    active = dy.int32(k_start) <= k

    linearRise = dy.convert( (k - dy.int32(k_start) ), dy.DataTypeFloat64(1) )
    activation = dy.convert( active, dy.DataTypeFloat64(1) )

    return activation * linearRise


def signal_impulse(k_event):
    """
        Pulse signal generator

        generates a unique pulse at sampling index k_event

        k_event - the sampling index at which the pulse appears
    """

    if k_event < 0:
        raise BaseException('The sampling index for the event is invalid (k_event < 0)')

    k = dy.counter()
    pulse_signal = dy.int32(k_event) == k

    return pulse_signal

def signal_periodic_impulse(period, phase):
    """
        signal generator for periodic pulses

        generates a sequence of pulses

        period - singal or constant describing the period in samples at which the pulses are generated
        phase  - singal or constant describing the phase in samples at which the pulses are generated
    """

    k = counter_triggered( upper_limit=dy.int32(period) - dy.int32(1), reset_on_limit=True )
    pulse_signal = dy.int32(phase) == k

    return pulse_signal



def signal_step_wise_sequence( time_instance_indices, values, time_scale=None, counter=None, reset=None ):
    """
        signal generator for a step-wise changeing signal

        time_instance_indices - an array of sampling instants at which the signal changes its values
        values                - an array of values; must have one more element than time_instance_indices
        time_scale            - multiplies all elements of time_instance_indices by the given factor (optional)
        counter               - an alternative sample counter (optional)
        reset                 - boolean signal to reset the sequence (optional)

        Example
        -------

        time_instance_indices = [      50, 100, 150, 250, 300, 350, 400,  450, 500  ]
        values                = [ 0, -1.0,   0, 1.0,  0, -1.0, 0,   0.2, -0.2, 0   ]

        v = step_wise_sequence( time_instance_indices, values )
    """
    
    if len(values) - 1 != len(time_instance_indices):
        raise BaseException( "len(values) - 1 != len(time_instance_indices)" )

    if counter is None:
        counter = dy.counter()

    indices_mem = dy.memory(datatype=dy.DataTypeInt32(1),   constant_array=time_instance_indices )
    values_mem  = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=values )

    current_index = dy.signal()

    current_time_index_to_check = dy.memory_read( indices_mem, current_index )

    # scale time
    if time_scale is not None:
        index_to_check = time_scale * current_time_index_to_check
    else:
        index_to_check = current_time_index_to_check

    # check wether to step to the next sample
    increase_index = dy.int32(0)
    increase_index = dy.conditional_overwrite(increase_index, counter >= index_to_check, dy.int32(1) )
    current_index << dy.counter_triggered(upper_limit=len(time_instance_indices), stepwidth=increase_index, reset=reset )

    val = dy.memory_read(values_mem, current_index)

    return val


def play( sequence_array,  stepwidth=None, initial_state = 0, reset=None, reset_on_end:bool=False, start_trigger=None, pause_trigger=None, auto_start:bool=True ):
    """
        playback of a sequence (TODO: update)

        returns sample, playback_index

        sequence_array           - the sequence given as a list of values
        reset                    - reset the playback and start from the beginning
        reset_on_end             - reset playback once the end is reached (repetitive playback)
        start_trigger            - event to start playback
        pause_trigger            - event to pause playback
        auto_start               - start playback automatically 


        return values

        sample                   - the value obtained from sequence_array
        playback_index           - the current position of playback (index of the currently issued sequence element)
    """

    sequence_array_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=sequence_array )

    # if prevent_initial_playback:
    #     initial_counter_state = np.size(sequence_array)
    # else:
        

    playback_index = counter_triggered( upper_limit=np.size(sequence_array)-1, 
                                        stepwidth=stepwidth, initial_state=initial_state, 
                                        reset=reset, reset_on_limit=reset_on_end, 
                                        start_trigger=start_trigger, pause_trigger=pause_trigger, 
                                        auto_start=auto_start)

    # sample the given data
    sample = dy.memory_read(sequence_array_storage, playback_index)

    return sample, playback_index




#
# Filters
#

def diff(u : dy.Signal, initial_state = None):
    """
        Discrete difference

        y = u[k] - u[k-1] 

        initial state

        u[0] = initial_state   in case initial_state is not None
        u[0] = 0               otherwise
    """

    i = dy.delay( u, initial_state )
    y = dy.add( [ i, u ], [ -1, 1 ] )

    return y

def sum(u : dy.Signal, initial_state=0, no_delay=False):
    """
        Accumulative sum

        The difference equation

            y[k+1] = y[k] + u[k]

        is evaluated. The return value is either

            y[k]   by default or when no_delay == False
        or

            y[k+1] in case no_delay == True .
    """

    y_k = dy.signal()
    
    y_kp1 = y_k + u

    y_k << dy.delay(y_kp1, initial_state=initial_state)

    if no_delay:
        return y_kp1
    else:
        return y_k

def sum2(u : dy.Signal, initial_state=0):
    """
        Accumulative sum

        The difference equation

            y[k+1] = y[k] + u[k]

        is evaluated. The return values are

            y[k], y[k+1]
    """

    y_k = dy.signal()
    
    y_kp1 = y_k + u

    y_k << dy.delay(y_kp1, initial_state=initial_state)

    return y_k, y_kp1

def euler_integrator( u : dy.Signal, Ts, initial_state = 0.0):
    """
        Euler (forward) integrator

        y[k+1] = y[k] + Ts * u[k]
    """

    yFb = dy.signal()

    if not isinstance( Ts, dy.SignalUserTemplate ): 
        i = dy.add( [ yFb, u ], [ 1, Ts ] )
    else:
        i = yFb + Ts * u

    y = dy.delay( i, initial_state )

    yFb << y

    return y

def dtf_lowpass_1_order(u : dy.Signal, z_infinity):
    """
        First-order discrete-time low pass filter

                 1 - z_infinity
        H (z) =  --------------
                 z - z_infinity
    """

    zinf = dy.float64( z_infinity )
    zinf_ = dy.float64( 1 ) - zinf

    y_delayed = dy.signal()
    y =  zinf * y_delayed + zinf_ * u

    y_delayed << dy.delay(y)
    
    return y

def transfer_function_discrete(u : dy.Signal, num_coeff : List[float], den_coeff : List[float] ):

    """
    Discrete time transfer function

    u         - input signal
    num_coeff - list of numerator coefficients of the transfer function
    den_coeff - list of denominator coefficients of the transfer function

    returns the output of the filter

    Details:
    --------

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



#
# Control
#

def PID_controller(r, y, Ts, kp, ki = None, kd = None):
    """
        discrete-time PID-controller

        r           - the reference signal
        y           - the measured plant output
        Ts          - the sampling time
        kp, ki, kd  - the controller parameters (proportional, integral, differential)
    """
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
