# OpenRTDynamics 2

-- Open Real-Time Dynamics 2 - A modelling framework for dynamic systems (http://openrtdynamics.github.io/)

OpenRTDynamics 2 is a framework to support implementing control systems, signals processing algorithms, and dynamic simulations in a framework of model-based design. Herein, block [diagrams](https://en.wikibooks.org/wiki/Control_Systems/Block_Diagrams), which are a common in control theory and signal processing, are used to build models. 
Provided is a python library for defining such systems and to generate code (c++) from them. Templates
can be used to adapt the generated code to different targets.

While the first version of this framework was built on top of the scientific computing language Scilab, the new, second
version now is based on Python.

Please note: in its current state, the library is considered experimental and the interface might be subjected to 
changes. Further, up to now, it is limited to discrete-time systems - no continuous ODE-integrators.

The following features are implemented

- basic signal processing: transfer functions, rate limiters, different signal sources, ...
- subsystems: loops, triggered systems
- state machines implemented in form of a set of subsystems of which one is active at a time
- execute models inside Python/Numpy (through code generation and just-in-time compilation thanks to [cppyy](https://cppyy.readthedocs.io/en/latest/)
- some templates for code generation: generic printf-based command-line, web assembly (to run in models in Javascript) 

## Installation

The framework ships with python's package manager, thus

    pip install openrtdynamics2
    
is sufficient. Alternatively, from within the cloned git folder

    pip install .
    
gives you the most recent revision.

For the html-export, the c++ compiler [emscripten](https://emscripten.org/) is required and the command 'emcc' must be accessible.

## Fundamental concepts: delays, initial values, and feedback loops

A simple model is given by

    y = dy.signal()                         # introduce variable y
    x = z + u                               # x[k] = z[k] + u[k]
    z << dy.delay(x, initial_state = 2.0)   # z[k+1] = x[k], z[0] = 2.0

Herein, a signal variable $z$ is introduced that is combined with the system input $u$. The resulting intermediate variable $x$ is then delayed and assigned to $z$ closing the feedback loop. The delay has an initial value $z[0] = 2.0$.

Given $u[k] = 1.0$, for $k>=0$, the output sequence for $y$ is then $\{ 2, 3, 4, 5, ...  \}$.

By combination of these elements (and potentially others), more sophisticated signal processing algorithms (filters, controllers, ...) can be implemented.

See also this [notebook](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/minimal_demo.ipynb) that contains a running example.

## Code Examples

A good starting point is given in [Simulation of controlled ODEs](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/pandemic_control.ipynb). Herein, some basic concepts are explained in an intuitive example.

## Missing pieces

This list might be considered as a list of things to do.

- In case there is a common name among the input and outputs of a system, compilation fails.
- Signals are limited to be single valued, i.e., vectorial signals are not implemented.
- If there is an unconnected input, the html export fails to run


## Background

Starting in 2008, OpenRTDynamics has been developed due to the lack of a suitable open-source alternative to the famous and powerful modelling tool Simulink (Mathworks). Within the years, the framework has evolved and applied in medical engineering reasearch. The language was based on the scientific programming language [Scilab](scilab.org). The models are executed by a real-time capable interpreter.

OpenRTDynamics 2 is a re-implementation for the popular Python language. Further, the former interpreter is replaced by code generation. Finally, some concepts which had shortcomings in the old version are improved as Python introduces a bigger amount of flexibility.
