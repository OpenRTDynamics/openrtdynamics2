import dynamics as dy

import os
import json

from colorama import init,  Fore, Back, Style
init(autoreset=True)

def eInt( u : dy.Signal, Ts : float, name : str):

    yFb = dy.signal()

    i = dy.add( [ yFb, u ], [ 1, Ts ] ).setNameOfOrigin(name + '_i (add)').setName(name + '_i')
    y = dy.delay( i ).setNameOfOrigin(name + '_y (delay)').setName(name + '_y')

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
    damping = dy.system_input( baseDatatype ).setName('damping')
    U = dy.system_input( baseDatatype ).setName('u')

    x = dy.signal()
    v = dy.signal()

    acc = dy.add( [ U, v, x ], [ 1, -0.5, -0.1 ] ).setNameOfOrigin('acceleration model')

    v << eInt( acc, Ts=0.1, name="intV").setName('x')
    x << eInt( v, Ts=0.1, name="intX").setName('v')

    # define the outputs of the simulation
    x.setName('x')
    v.setName('v')

    # define output variables
    outputSignals = [ x,v ]

    # compile this system
    compileResults = dy.compile_current_system(outputSignals)

    # 
    lib = dy.SystemLibrary(compileResults)

    # print(lib.sourceCode)

    dy.leave_system()

    return lib
    


oscillator = define_system_oscillator()


