from typing import Dict, List
from . import lang as dy


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

        print("counter cache hits ***: " + str(self.hits) )
        return self.counter_signal_



def counter():
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


# def counter():

#     increase = dy.const(1, dy.DataTypeInt32(1) )
#     cnt = dy.signal()
#     tmp = dy.delay(cnt + increase)
#     cnt << tmp 

#     return tmp


# def dtf_lowpass_1_order(u : dy.Signal, z_infinity : float):

#     zinf = dy.float64( z_infinity )
#     zinf_ = dy.float64( 1 - z_infinity )

#     y = dy.signal()

#     y << dy.delay( zinf * y + zinf_ * u )

#     return y


def dtf_lowpass_1_order(u : dy.Signal, z_infinity : float):

    zinf = dy.float64( z_infinity )
    zinf_ = dy.float64( 1 - z_infinity )

    y_delayed = dy.signal()
    y =  zinf * y_delayed + zinf_ * u

    y_delayed << dy.delay(y)
    
    return y



def dtf_filter(u : dy.Signal, num_coeff : List[float], den_coeff : List[float] ):

    """

    Realize a discrete-time transfer function by using 'direct form II'

            b0 + b1 z^-1 + b2 z^-2 + ... + bN z^-N
    H(z) = ----------------------------------------
             1 + a1 z^-1 + a2 z^-2 + ... + aM z^-M

    c.f. https://en.wikipedia.org/wiki/Digital_filter

    The coefficients are encoded as follows:

    num_coeff = [b0, b1, .., bN]
    den_coeff = [a1, a2, ... aM] 
    
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

    i = dy.delay( u )
    y = dy.add( [ i, u ], [ -1, 1 ] )

    return y

def sum(u : dy.Signal):

    y = dy.signal()    
    y << dy.delay(y + u)

    return y

def step(k_step : int):
    k = dy.counter()
    y = dy.int32(k_step) <= k

    return y

def ramp(k_start : int):
    # TODO
    k = dy.counter()
    active = dy.int32(k_start) <= k

    linearRise = dy.convert( (k - dy.int32(k_start) ), dy.DataTypeFloat64(1) )
    activation = dy.convert( active, dy.DataTypeFloat64(1) )

    return activation * linearRise



