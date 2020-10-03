
import math
import matplotlib.pylab as plt
import numpy as np

#from path_generation import *
from . import path_generation as pg

# example input data
A=np.array( 
    [[0,0.0], 
    [5,0],
    [15,3.0],
    [25,3.0],
    [35,3.0],
    [40,3.0-5],
    [40,3.0-10],
    [40,3.0-20],
    [30,3.0-30],
    [20,3.0-30],
    [10,3.0-20],
    [00,3.0-20],
    [-10,3.0-20],
    [-20,3.0-20],
    [-30,3.0-20],
    [-40,3.0-20],
    ]     )

X = A[:,0]
Y = A[:,1]

# run simulation
Nmax, output, sim_results = pg.generate_path(X=X, Y=Y, N=300000, wheelbase=1.0, Delta_d_reference=0.1, lr=2.0)


# pg.plot_generator_result( X, Y, output )
