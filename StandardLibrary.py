
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


def counter():
    # TODO: create only one counter per simulation? Needs to store some context info somewhere to do so.

    increase = dy.const(1, dy.DataTypeInt32(1) )
    cnt = dy.signal()
    tmp = dy.delay(cnt + increase)
    cnt << tmp 

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



