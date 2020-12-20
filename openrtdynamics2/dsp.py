import math

from typing import Dict, List
from . import lang as dy
import numpy as np



import control as cntr




# the base variable for discrete-time transfer functions 
z = cntr.TransferFunction([1,0], [1], True)


def z_tf(u, H):
    """
        discrete-time transfer function

        u  - the input signal
        L  - the transfer function
    """

    def get_zm1_coeff(L):
    
        numcf = L.num[0][0]
        dencf = L.den[0][0]
        
        N = len(dencf)-1
        M = len(numcf)-1

        # convert to normalized z^-1 representation
        a0 = dencf[0]
        
        numcf_ = np.concatenate( [np.zeros(N-M), numcf] ) / a0
        dencf_ = dencf[1:] / a0
        
        return numcf_, dencf_


    # convert the transfer function T to the representation needed for dy.transfer_function_discrete
    b, a = get_zm1_coeff(H)

    # implement the transfer function
    y = dy.transfer_function_discrete(u, num_coeff=b, den_coeff=a )

    return y
