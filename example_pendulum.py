import openrtdynamics2.lang as dy

import os
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)


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


# define system inputs
friction       = dy.system_input( baseDatatype ).set_name('friction')   * dy.float64(0.05)
mass           = dy.system_input( baseDatatype ).set_name('mass')       * dy.float64(0.05)

J = dy.float64(1.0)
l = dy.float64(1.0)

# create placeholder for the plant output signal
angle = dy.signal()
angular_velocity = dy.signal()


angular_acceleration =  dy.float64(9.81) * mass/l * dy.sin(angle).set_blockname('sinus') - friction * angular_velocity


sampling_rate = 0.01
angular_velocity_ = euler_integrator(angular_acceleration, sampling_rate, 0.0)
angle_            = euler_integrator(angular_velocity_,    sampling_rate, 0.0)

angle             << angle_
angular_velocity  << angular_velocity_

# main simulation ouput
dy.set_primary_outputs([ angle, angular_velocity ])


sourcecode, manifest = dy.generate_code(template=dy.WasmRuntime(), folder="generated/", build=True)

# print the sourcecode (main.cpp)
print(Style.DIM + sourcecode)

dy.clear()
