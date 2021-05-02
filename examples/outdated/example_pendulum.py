import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)

import math


#
# Enter a new system (simulation)
#
system = dy.enter_system()
baseDatatype = dy.DataTypeFloat64(1) 

# define a function that implements a discrete-time integrator
def euler_integrator( u : dy.Signal, sampling_rate : float, initial_state = 0.0):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, sampling_rate ] )
    y = dy.delay( i, initial_state )

    yFb << y

    return y


ofs = dy.float64(0.1).set_name('ofs')

# define system inputs
friction       = dy.system_input( baseDatatype ).set_name('friction')   * dy.float64(0.05) + ofs
mass           = dy.system_input( baseDatatype ).set_name('mass')       * dy.float64(0.05) + ofs
length         = dy.system_input( baseDatatype ).set_name('length')     * dy.float64(0.05) + ofs


# length = dy.float64(0.3)
g = dy.float64(9.81).set_name('g')

# create placeholder for the plant output signal
angle = dy.signal()
angular_velocity = dy.signal()


angular_acceleration =  dy.float64(0) - g / length * dy.sin(angle) - (friction / (mass * length) ) * angular_velocity

angular_acceleration.set_name('angular_acceleration')

sampling_rate = 0.01
angular_velocity_ = euler_integrator(angular_acceleration, sampling_rate, 0.0).set_name('ang_vel')
angle_            = euler_integrator(angular_velocity_,    sampling_rate, 30.0 / 180.0 * math.pi).set_name('ang')

angle             << angle_
angular_velocity  << angular_velocity_

# main simulation ouput
dy.set_primary_outputs([ angle, angular_velocity ])


sourcecode, manifest = dy.generate_code(template=dy.TargetWasm(), folder="generated/", build=True)

# print the sourcecode (main.cpp)
print(Style.DIM + sourcecode)

dy.clear()
