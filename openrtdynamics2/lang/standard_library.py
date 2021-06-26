import math

import typing as t
from . import lang as dy
from .signal_interface import SignalUserTemplate
import numpy as np

from .core_blocks import generic_subsystem, const, gain, convert, add, operator1, logic_and, logic_or, logic_xor, bitwise_and, bitwise_or, bitwise_shift_left, bitwise_shift_right, comparison, switchNto1, conditional_overwrite, if_else, sqrt, sin, cos, tan, atan, asin, acos, abs, logic_not, bitwise_not, atan2, pow, fmod, generic_cpp_static, flipflop, memory, memory_read, delay__, cpp_allocate_class, cpp_call_class_member_function



#
# constants
#

def int32(value):
    """Cast anything to DataTypeInt32

    Convert the input value to a signal.

    Parameters
    ----------
    value : SignalUserTemplate, int
        the signal or a constant value to convert to a signal

    Returns
    -------
    SignalUserTemplate
        the signal of type int32

    """

    if isinstance(  value, SignalUserTemplate ):
        # already a singal
        return value
    else:
        # create a new constant
        return dy.const(value, dy.DataTypeInt32(1) )

def float64(value):
    """Cast anything to DataTypeFloat64

    Convert the input value to a signal.

    Parameters
    ----------
    value : SignalUserTemplate, float
        the signal or a constant value to convert to a signal

    Returns
    -------
    SignalUserTemplate
        the signal of type float64

    """
    if isinstance(  value, SignalUserTemplate ):
        # already a singal
        return value
    else:
        # create a new constant
        return dy.const(value, dy.DataTypeFloat64(1) )


def boolean(value):
    """Cast anything to DataTypeBoolean

    Convert the input value to a signal.

    Parameters
    ----------
    value : SignalUserTemplate, int
        the signal or a constant value to convert to a signal

    Returns
    -------
    SignalUserTemplate
        the signal of type boolean

    """
    if isinstance(  value, SignalUserTemplate ):
        # already a singal
        return value
    else:
        # create a new constant
        if type(value) is bool:
            if value:
                v = 1
            else:
                v = 0

        elif type(value) is int:
            v = value

        return dy.const(v, dy.DataTypeBoolean(1) )



#
#
#

def initial_event():
    """Emits an event on the first sampling instant after the reset of the system

    Returns
    -------
    SignalUserTemplate
        the signal of type boolean containing the event
    """

    # TODO: introduce caching like done for counter()

    return dy.counter() == int32(0)


#
# Delay - the basis for all dynamic elements
#
def delay(u , initial_state = None):
    """Unit delay

    Delay the input u by one sampling instant:

        y[k+1] = u[k], y[0] = initial_state

    Parameters
    ----------
    u : SignalUserTemplate
        the input signal to delay
    initial_state : SignalUserTemplate
        the initial state (signal or constant value)

    Returns
    -------
    SignalUserTemplate
        the one-step delayed input   

    """

    if not isinstance( initial_state, SignalUserTemplate ):
        return dy.delay__( u, initial_state )

    else:

        event_on_first_sample = initial_event()

        delayed_input = dy.delay__( u, None )
        delayed_input = dy.conditional_overwrite( delayed_input, event_on_first_sample, initial_state )

        return delayed_input

def sample_and_hold(u, event, initial_state = None):
    """Sample & hold

    Samples the input when event is true and hold this value for the proceeding time instants. 

    Parameters
    ----------
    u : SignalUserTemplate
        the input to sample
    event : SignalUserTemplate
        the event on which sampling of the input is performed
    initial_state : SignalUserTemplate
        the initial output

    Returns
    -------
    SignalUserTemplate
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
    """Unwrap an angle

    Unwrap and normalize the input angle to the range 

           [0, 2*pi[     in case normalize_around_zero == false
        or [-pi, pi]     in case normalize_around_zero == true


    Parameters
    ----------

    angle : SignalUserTemplate
        the input signal (angle in radians)

    Returns
    -------
    SignalUserTemplate
        the output signal   

    """

    def normalize_around_zero(angle):
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
        return normalize_around_zero(unwrapped_angle)
    else:
        return unwrapped_angle





def saturate(u, lower_limit = None, upper_limit = None):
    """Saturation

    The output is the saturated input

    Parameters
    ----------

    lower_limit : SignalUserTemplate
        lower bound for the output 
    upper_limit : SignalUserTemplate
        upper bound for the output

    Returns
    -------
    SignalUserTemplate
        the integer output signal 

    Details
    -------
            { lower_limit   for u < lower_limit
        y = { u             otherwise
            { upper_limit  for u > upper_limit
    """

    y = u

    if lower_limit is not None:
        y = dy.conditional_overwrite( y, y < float64(lower_limit), lower_limit )
    
    if upper_limit is not None:
        y = dy.conditional_overwrite( y, y > float64(upper_limit), upper_limit )

    return y


def rate_limit( u, Ts, lower_limit, upper_limit, initial_state = 0 ):
    """Rate limiter

    Parameters
    ----------

    Ts : SignalUserTemplate
        sampling time (constant)
    lower_limit : SignalUserTemplate
        lower rate limit
    upper_limit : SignalUserTemplate
        upper rate limit

    Returns
    -------
    SignalUserTemplate
        the output signal    

    """

    Ts_ = float64(Ts)

    y = dy.signal()

    omega = u - y
    omega_sat = saturate(omega, float64(lower_limit) * Ts_, float64(upper_limit) * Ts_)
    y << euler_integrator( omega_sat, 1, initial_state=initial_state)

    return y


#
# Counters
#

# TODO: mark as private
class __Counter():
    """
        This class is meant to store the counter output signal as it might be used
        by more than one destination block. The instance of this class is per simulation
        and will be stored in the components property of the current get_system_context()
    """
    def __init__(self, counter_signal : SignalUserTemplate):
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
    """Basic counter - the sampling index k

    The integer output is increasing with each sampling instant by 1.
    Counting starts at zero.

    Returns
    -------
    SignalUserTemplate
        the integer output signal describing the sampling index k

    """

    if not 'counter' in dy.get_current_system().components:
        # no counter has been defined in this system so far. Hence, create one.

        increase = dy.const(1, dy.DataTypeInt32(1) ).set_name('cnt_increase')
        cnt = dy.signal()
        tmp = dy.delay(cnt + increase)
        cnt << tmp 

        tmp.set_name('shared_counter')

        # store the output signal of the counter as it might be used again. 
        dy.get_current_system().components['counter'] = __Counter(tmp)

    else:
        # use the output of an already created counter
        tmp = dy.get_current_system().components['counter'].output

    return tmp





def counter_triggered( upper_limit, stepwidth=None, initial_state = 0, reset=None, reset_on_limit:bool=False, start_trigger=None, pause_trigger=None, auto_start:bool=True, no_delay:bool=False ):
    """A generic counter

    Features:
    - upper limit
    - triggerable start/pause
    - resetable
    - dynamic adjustable step-size

    Parameters
    ----------

    upper_limit : int
        the upper limit of the counter
    initial_state : int
        the state after reset
    reset : SignalUserTemplate
        reset the counter
    reset_on_limit : bool
        reset counter once the upper limit is reached
    start_trigger : SignalUserTemplate
        event to start counting
    pause_trigger : SignalUserTemplate
        event to pause counting
    auto_start : bool
        start counting automatically
    no_delay : bool
        when True the new value of the counter is returned without delay 

    Returns
    -------
    SignalUserTemplate
        the boolean output signal 
    SignalUserTemplate
        event that fires when the upper limit of the counter is reached 
        
    """

    if stepwidth is None:
        stepwidth = dy.int32(1)

    counter = dy.signal()

    reached_upper_limit = counter >= dy.int32(upper_limit)

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
    paused =  dy.flipflop(activate_trigger=activate_trigger, disable_trigger=start_trigger, initial_state = not auto_start, no_delay=True).set_name('paused')

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
        return counter, reached_upper_limit
    else:
        return new_counter, reached_upper_limit





def toggle(trigger, initial_state=False, no_delay=False):
    """Toggle a state based on an event

    Parameters
    ----------

    period : SignalUserTemplate
        the signal to trigger a state change
    initial_state : int
        the initial state
    no_delay : bool
        when true the toggle immediately reacts to a trigger (default: false)

    Returns
    -------
    SignalUserTemplate
        the boolean state signal

    SignalUserTemplate
        the event for activation
    SignalUserTemplate
        the event for deactivation

    

    """

    state = dy.signal()

    activate   = dy.logic_and( dy.logic_not( state ), trigger )
    deactivate = dy.logic_and( trigger , state)

    state_ = dy.flipflop( activate, deactivate, 
                            initial_state = 0, 
                            no_delay=no_delay )

    if not no_delay:
        state << state_
    else:
        state << dy.delay(state_)


    return state_, activate, deactivate
    

#
# signal generators
#

def signal_square(period, phase):
    """Square wave signal generator

    Parameters
    ----------

    period : SignalUserTemplate
        singal or constant describing the period in samples at which the edges of the square are placed
    phase : SignalUserTemplate
        singal or constant describing the phase in samples at which the edges of the square are placed

    Returns
    -------
    SignalUserTemplate
        the output signal

    """
    trigger = signal_periodic_impulse(period, phase)


    # k, trigger = counter_triggered( upper_limit=dy.int32(period) - dy.int32(1), reset_on_limit=True )

    state, activate, deactivate = toggle(trigger, no_delay=True)

    return state, activate, deactivate


def signal_sinus(N_period : int = 100, phi = None):
    """Sine wave generator

    Parameters
    ----------
    N_period : SignalUserTemplate
        period in sampling instants (type: constant integer)
    phi : SignalUserTemplate
        phase shift (signal)

    Returns
    -------
    SignalUserTemplate
        the output signal

    Details
    -------
    The output is computed as follows:

    y = sin( k * (1 / N_period * 2 * pi) + phi )

    k - is the sampling index

    """

    if N_period <= 0:
        raise BaseException('N_period <= 0')

    if phi is None:
        phi = dy.float64(0.0)

    i, _ = dy.counter_triggered( upper_limit=N_period-1, reset_on_limit=True )
    y = dy.sin( i * dy.float64(1/N_period * 2*math.pi) + phi )

    return y

def signal_step(k_step):
    """Signal generator for a step signal

    Parameters
    ----------
    k_step : SignalUserTemplate
        the sampling index as returned by counter() at which the step appears.

    Returns
    -------
    SignalUserTemplate
        the output signal
    """
    k = dy.counter()
    y = dy.int32(k_step) <= k

    return y

def signal_ramp(k_start):
    """Signal generator for a ramp signal

    Parameters
    ----------
    k_start : SignalUserTemplate
        the sampling index as returned by counter() at which the ramp starts increasing.

    Returns
    -------
    SignalUserTemplate
        the output signal

    Details
    -------

        y[k] = { 0           for k <  k_start
               { k-k_start   for k >= k_start
    """
    k = dy.counter()
    active = dy.int32(k_start) <= k

    linearRise = dy.convert( (k - dy.int32(k_start) ), dy.DataTypeFloat64(1) )
    activation = dy.convert( active, dy.DataTypeFloat64(1) )

    return activation * linearRise


def signal_impulse(k_event):
    """Pulse signal generator

    Generates a unique pulse at the sampling index k_event.

    Parameters
    ----------
    k_event : SignalUserTemplate
        the sampling index at which the pulse appears


    Returns
    -------
    SignalUserTemplate
        the output signal
    """

    if k_event < 0:
        raise BaseException('The sampling index for the event is invalid (k_event < 0)')

    k = dy.counter()
    pulse_signal = dy.int32(k_event) == k

    return pulse_signal

def signal_periodic_impulse(period, phase):
    """Signal generator for periodic pulses

    Parameters
    ----------

    period : SignalUserTemplate
        singal or constant describing the period in samples at which the pulses are generated
    phase : SignalUserTemplate
        singal or constant describing the phase in samples at which the pulses are generated

    Returns
    -------
    SignalUserTemplate
        the output signal

    """

    k, trigger = counter_triggered( upper_limit=dy.int32(period) - dy.int32(1), reset_on_limit=True )
    pulse_signal = dy.int32(phase) == k

    return pulse_signal



def signal_step_wise_sequence( time_instance_indices, values, time_scale=None, counter=None, reset=None ):
    """Signal generator for a step-wise changeing signal

    Parameters
    ----------

    time_instance_indices : List[int]
        an array of sampling instants at which the signal changes its values
    values : List[float]
        an array of values; must have one more element than time_instance_indices
    time_scale : SignalUserTemplate
        multiplies all elements of time_instance_indices by the given factor (optional)
    counter : SignalUserTemplate
        an alternative sample counter (optional), default: counter=dy.counter()
    reset : SignalUserTemplate
        boolean signal to reset the sequence (optional)

    Returns
    -------
    SignalUserTemplate
        the output signal

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

    cnt_, _ = dy.counter_triggered(upper_limit=len(time_instance_indices), stepwidth=increase_index, reset=reset )
    current_index << cnt_
    val = dy.memory_read(values_mem, current_index)

    return val


def play( sequence_array,  stepwidth=None, initial_state = 0, reset=None, reset_on_end:bool=False, start_trigger=None, pause_trigger=None, auto_start:bool=True, no_delay:bool=False ):
    """Play a given sequence of samples

    Parameters
    ----------

    sequence_array : list[float]
        the sequence given as a list of values
    reset : SignalUserTemplate
        reset playback and start from the beginning
    reset_on_end : SignalUserTemplate
        reset playback once the end is reached (repetitive playback)
    start_trigger : SignalUserTemplate
        event to start playback
    pause_trigger : SignalUserTemplate
        event to pause playback
    auto_start : bool
        start playback automatically 


    Returns
    -------
    SignalUserTemplate
        the value obtained from sequence_array
    SignalUserTemplate
        the current position of playback (index of the currently issued sequence element)


    """

    sequence_array_storage = dy.memory(datatype=dy.DataTypeFloat64(1), constant_array=sequence_array )

    # if prevent_initial_playback:
    #     initial_counter_state = np.size(sequence_array)
    # else:
        

    playback_index, _ = counter_triggered(
        upper_limit=np.size(sequence_array)-1, 
        stepwidth=stepwidth, initial_state=initial_state, 
        reset=reset, reset_on_limit=reset_on_end, 
        start_trigger=start_trigger, pause_trigger=pause_trigger, 
        auto_start=auto_start,
        no_delay=no_delay
    )

    # sample the given data
    sample = dy.memory_read(sequence_array_storage, playback_index)

    return sample, playback_index




#
# Filters
#

def diff(u : SignalUserTemplate, initial_state = None):
    """Discrete difference

    Parameters
    ----------

    u : SignalUserTemplate
        the input signal
    initial_state : float, SignalUserTemplate
        the initial state

    Returns
    -------
    SignalUserTemplate
        the output signal of the filter

    Details:
    --------

    y = u[k] - u[k-1] 

    initial state

    u[0] = initial_state   in case initial_state is not None
    u[0] = 0               otherwise
    """

    i = dy.delay( u, initial_state )
    y = dy.add( [ i, u ], [ -1, 1 ] )

    return y

def sum(u : SignalUserTemplate, initial_state=0, no_delay=False):
    """Accumulative sum

    Parameters
    ----------

    u : SignalUserTemplate
        the input signal
    initial_state : float, SignalUserTemplate
        the initial state
    no_delay : bool
        when true the output is not delayed

    Returns
    -------
    SignalUserTemplate
        the output signal of the filter

    Details:
    --------

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

def sum2(u : SignalUserTemplate, initial_state=0):
    """Accumulative sum

    Parameters
    ----------

    u : SignalUserTemplate
        the input signal
    initial_state : float, SignalUserTemplate
        the initial state

    Returns
    -------
    SignalUserTemplate
        the output signal of the filter

    Details:
    --------

    The difference equation

        y[k+1] = y[k] + u[k]

    is evaluated. The return values are

        y[k], y[k+1]
    """

    y_k = dy.signal()
    
    y_kp1 = y_k + u

    y_k << dy.delay(y_kp1, initial_state=initial_state)

    return y_k, y_kp1

def euler_integrator( u : SignalUserTemplate, Ts, initial_state = 0.0, lower_limit = None, upper_limit = None):
    """Euler (forward) integrator

    Parameters
    ----------

    u : SignalUserTemplate
        the input signal
    Ts : float
        the sampling time
    initial_state : float, SignalUserTemplate
        the initial state of the integrator (optional)
    lower_limit : SignalUserTemplate
        lower bound for the integrator state (optional)
    upper_limit : SignalUserTemplate
        upper bound for the integrator state (optional)

    Returns
    -------
    SignalUserTemplate
        the output signal of the filter

    Details:
    --------

        y[k+1] = y[k] + Ts * u[k]
    """

    yFb = dy.signal()

    if not isinstance( Ts, SignalUserTemplate ): 
        i = dy.add( [ yFb, u ], [ 1, Ts ] )
    else:
        i = yFb + Ts * u

    y = dy.delay( 
        dy.saturate( i, lower_limit=lower_limit, upper_limit=upper_limit ), 
        initial_state
    )

    yFb << y

    return y



def dtf_lowpass_1_order(u : SignalUserTemplate, z_infinity):
    """First-order discrete-time low pass filter

    Parameters
    ----------

    u : SignalUserTemplate
        the input signal

    Returns
    -------
    SignalUserTemplate
        the output signal of the filter

    Details:
    --------

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

def transfer_function_discrete(u : SignalUserTemplate, num_coeff : t.List[float], den_coeff : t.List[float] ):

    """Discrete time transfer function

    Parameters
    ----------
    u : SignalUserTemplate
        the input signal
    num_coeff : List[float]
        a list of numerator coefficients of the transfer function
    den_coeff : List[float]
        a list of denominator coefficients of the transfer function

    Returns
    -------
    SignalUserTemplate
        the output signal of the filter

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

        z_iterate = dy.delay( z_iterate ) .extend_name('_z' + str(i) )
        z_.append( z_iterate ) 


    # build feedback path
    #
    # a1 = den_coeff[0]
    # a2 = den_coeff[1]
    # a3 = den_coeff[2]
    #        ...
    sum_feedback = u
    for i in range(0,N):

        a_ip1 = dy.float64( den_coeff[i] ).extend_name('_a' + str(i+1) )

        sum_feedback = sum_feedback - a_ip1 * z_[i]

    sum_feedback.extend_name('_i')


    # close the feedback loop
    z_pre << sum_feedback

    # build output path
    #
    # b0 = num_coeff[0]
    # b1 = num_coeff[1]
    # b2 = num_coeff[2]
    #        ...    
    for i in range(0,N+1):
        
        b_i = dy.float64( num_coeff[i] ).extend_name('_b' + str(i) )

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
    """Discrete-time PID-controller

    Parameters
    ----------
    r : SignalUserTemplate
        the reference signal
    y : SignalUserTemplate
        the measured plant output
    Ts : float
        the sampleing time
    kp : float
        the parameter kp (proportional)
    ki : float
        the parameter ki (integral)
    kd : float
        the parameter kd (differential)

    Returns
    -------
    SignalUserTemplate
        the control variable u

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
