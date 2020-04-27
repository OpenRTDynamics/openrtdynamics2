import dynamics as dy

import os
import json

from colorama import init,  Fore, Back, Style
init(autoreset=True)

def eueler_integrator( u : dy.Signal, Ts : float, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, Ts ] ).set_blockname(name + '_i (add)').set_name(name + '_i')
    y = dy.delay( i ).set_blockname(name + '_y (delay)').set_name(name + '_y')

    yFb << y 

    return y


#
# Define library systems
#

def define_system_oscillator():
    dy.enter_system('oscillator')

    print(dy.get_simulation_context())

    baseDatatype = dy.DataTypeFloat64(1) 

    # input to the system
    damping = dy.system_input( baseDatatype ).set_name('damping')
    U = dy.system_input( baseDatatype ).set_name('u')

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -0.5, -0.1 ] ).set_blockname('acceleration model')
    acc.set_name('acc')

    v << eueler_integrator( acc, Ts=0.1, name="intV").set_name('x')
    x << eueler_integrator( v, Ts=0.1, name="intX").set_name('v')

    # define the outputs of the simulation
    x.set_name('x')
    v.set_name('v')

    # define output variables
    outputSignals = [ x,v ]

    # set the outputs of the system
    dy.set_primary_outputs(outputSignals)

    # compile this system
    compileResults = dy.compile_current_system()

    # add to library
    lib = dy.SystemLibraryEntry(compileResults)

    # print(lib.sourceCode)

    dy.leave_system()

    return lib
    


oscillator = define_system_oscillator()


