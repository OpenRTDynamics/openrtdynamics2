# OpenRTDynamics 2

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/OpenRTDynamics/openrtdynamics2/HEAD)

Open Real-Time Dynamics 2 - A modelling framework for dynamic systems 

http://openrtdynamics.github.io/

OpenRTDynamics 2 is a framework to support implementing control systems, signals processing algorithms, and dynamic simulations in a framework of model-based design. Herein, block [diagrams](https://en.wikibooks.org/wiki/Control_Systems/Block_Diagrams), which are a common in control theory and signal processing, are used to build models. 
Provided is a python library for defining such systems and to generate code (c++) from them. Templates
can be used to adapt the generated code to different targets.

While the first version of this framework was built on top of the scientific computing language Scilab, the new, second
version now is based on Python.

Please note: in its current state, the library is considered experimental and the interface might be subjected to 
changes. Further, up to now, it is limited to discrete-time systems - no continuous ODE-integrators.

The following features are implemented

- basic signal processing: transfer functions, rate limiters, different signal sources, ...
- conrtol structures acting on subsystems: loops, triggered systems (if statements)
- state machines implemented in form of a set of subsystems of which one is active at a time
- a simulator to execute models inside Python/Numpy (through code generation and just-in-time compilation thanks to [cppyy](https://cppyy.readthedocs.io/en/latest/)
- some templates for code generation: generic printf-based command-line, web assembly (to run in models in Javascript) 

## Installation

The framework can be installed with python's package manager (pip):

    pip install openrtdynamics2
    
Alternatively, from the cloned git folder can be installed like this:

    pip install .
    
Optional: For the html-export, the c++ compiler [emscripten](https://emscripten.org/) is required and the command 'emcc' must be accessible.

## Fundamental concepts: delays, initial values, and feedback loops

A simple model is given by

    y = dy.signal()                         # introduce variable y
    x = z + u                               # x[k] = z[k] + u[k]
    z << dy.delay(x, initial_state = 2.0)   # z[k+1] = x[k], z[0] = 2.0

Herein, a signal variable $z$ is introduced that is combined with the system input u. The resulting intermediate variable x is then delayed and assigned to z closing the feedback loop. The delay has an initial value z[0] = 2.0.

Given u[k] = 1.0, for k>=0, the output sequence for y is then { 2, 3, 4, 5, ...  }.

By combination of these elements (and potentially others), more sophisticated signal processing algorithms (filters, controllers, ...) can be implemented.

See also this [notebook](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/minimal_demo.ipynb) that contains a running example.

Please note that ORTD does not work like traditional programming language in which execution processes from the top to the bottom eventually controlled by loops, if, etc. Though in some cases this might be true, the execution order of the individual blocks is automatically determined based their inter-dependencies among each other. Those dependencies are defined by the connections represented by signals.

## Numpy interface

For convenient design and rapid prototyping, models can be executed directly inside the Python environment taking Numpy arrays as in- and outputs. I.e., the fastest way to run a simulation of a model in Python is given by the following example:

    import numpy as np
    import openrtdynamics2.lang as dy
    from openrtdynamics2.ORTDtoNumpy import ORTDtoNumpy

    @ORTDtoNumpy()
    def low_pass( u, z_inf ):
        y = dy.dtf_lowpass_1_order(u, z_inf)
        return y

    y1 = low_pass( np.ones(100), 0.9 )

    # y1 is a numpy array containing the data for the output signal y

A more detailed insight can be obtained in [example](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/numpy_interface.ipynb).

## Example Models

A good starting point is given in [Simulation of controlled ODEs](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/pandemic_control.ipynb). Herein, some basic concepts are explained in an intuitive example.

A more [sophisticated example](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/interpolation_of_async_data.ipynb) demonstrates the control structures (if, loop, state machines) in a practically relevant setting in which asynchronous input trajectories shall be sampled and interpolated.  

Further, you might have a look into the [tests folder](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/tests), that serves as a reference containing a lot of examples for basic functions. 

All examples can be executed and modified online at [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/OpenRTDynamics/openrtdynamics2/HEAD). (Please note that the site might take some time to load)

## Generated code

The example above also explains how to use the generated source code which basically consists of a set of c++ classes. The memory layout is static (i.e., no calls to malloc/new are required). Thus, it should be convenient to embed the generated code into almost any target that understands traditional c++, for example, micro-controllers, nodes in the Robot Operating System (ROS) or any codebase written in c++.

## Documentation

For the available blocks and other functions, an [auto generated documentation](https://openrtdynamics.github.io/openrtdynamics2/generated/) is given for reference purposes (a cleanup of the (auto-) formatting is needed though). The information is also available via the doc-strings, thus also shown in various editors (e.g., by pressing Shift-Tab in Juypter).

## Algebraic loop

Watch out for algebraic loops! (More information in comming soon)

## Custom code

Sensors, actuators, means of communication, external libraries, and any other kind of functionality that provides a c/c++ interface can be embedded into custom blocks.  Custom (c++) code can be implemented into diagrams in form of user-provided c++ classes. See [Custom code](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/custom_cpp_code.ipynb) for examples and documentation.

## Custom targets

In the most simple form, the generated source code can simply be copy & pasted into the user's project. However, in addition target templates can be specified to automatically generate libraries or executables for various targets (e.g., a command line program, a library for the web, ...). Target types can also be implemented by the user.

To come..

## Missing pieces

This list might be considered as a list of things to do.

- In case there is a common name among the input and outputs of a system, compilation fails.
- Signals are limited to be single valued, i.e., vectorial signals are not implemented.
- If there is an unconnected input, the html export fails to run

## Background

Starting in 2008, OpenRTDynamics has been developed due to the lack of a suitable open-source alternative to the famous and powerful modelling tool Simulink (Mathworks). Within the years, the framework has evolved and applied in medical engineering research. The language was based on the scientific programming language [Scilab](scilab.org). The models are executed by a real-time capable interpreter.

OpenRTDynamics 2 is a re-implementation for the popular Python language. Further, the former interpreter is replaced by code generation. Finally, some concepts which had shortcomings in the old version are improved as Python introduces a bigger amount of flexibility.
