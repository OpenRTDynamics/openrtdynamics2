
import dynamics as dy




def counter():

    increase = dy.const(1, dy.DataTypeInt32(1) )

    cnt = dy.signal()
    
    cnt << dy.delay(cnt + increase)

    return cnt


