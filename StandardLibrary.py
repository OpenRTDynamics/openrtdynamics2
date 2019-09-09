
import dynamics as dy


def int32(value : int):
    return dy.const(value, dy.DataTypeInt32(1) )

def float64(value : int):
    return dy.const(value, dy.DataTypeFloat64(1) )

def boolean(value : int):
    return dy.const(value, dy.DataTypeBoolean(1) )


# def counter():
#     # TODO: create only one counter per simulation? Needs to store some context info somewhere to do so.

# TODO: This does not work as cnt (anonymous) will go into the graph traversion algs directly


#     increase = dy.const(1, dy.DataTypeInt32(1) )
#     cnt = dy.signal()
#     cnt << dy.delay(cnt + increase)

#     return cnt


class Counter():
    """
        This class is meant to store the counter output signal as it might be used
        by more than one destination block. The instance of this class is per simulation
        and will be stored in the components property of the current get_simulation_context()
    """
    def __init__(self, counter_signal):
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

        tmp.setName('main_couter')

        # store the output signal of the counter as it might be used again. 
        dy.get_simulation_context().components['counter'] = Counter(tmp)

    else:
        # use the output of an already created counter
        tmp = dy.get_simulation_context().components['counter'].output

    return tmp





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

    # k.setName('k')

    active = dy.int32(k_start) <= k

    # active.setName('active')

    # y = dy.convert( (k - dy.int32(k_start)), dy.DataTypeFloat64(1) ) * dy.convert( active, dy.DataTypeFloat64(1) ) 

    # return y

    linearRise = dy.convert( (k - dy.int32(k_start) ), dy.DataTypeFloat64(1) )  # .setName('linearRise')
    activation = dy.convert( active, dy.DataTypeFloat64(1) )  #.setName('activation')

    return activation * linearRise



