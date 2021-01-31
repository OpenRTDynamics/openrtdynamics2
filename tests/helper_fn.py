import numpy as np

def assert_equal( x, y ):
    
    assert np.size(np.where(( x == np.array( y )) == False)) == 0
    
    
def assert_approx(x, y, eps=0.00001):

    assert np.size(np.where(  np.abs( x - np.array(y) ) > eps )  ) == 0
