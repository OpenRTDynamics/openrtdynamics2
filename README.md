# OpenRTDynamics 2

Live demo: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/OpenRTDynamics/openrtdynamics2/HEAD)

Open Real-Time Dynamics 2 - A modeling framework for dynamic systems 

http://openrtdynamics.github.io/

OpenRTDynamics 2 is a framework to support implementing control systems, signals processing algorithms, and dynamic simulations in a framework of model-based design. Herein, block [diagrams](https://en.wikibooks.org/wiki/Control_Systems/Block_Diagrams), which are a common in control theory and signal processing, are used to build models. 
Provided is a python library for defining such systems and to generate code (c++) from them. Templates
can be used to adapt the generated code to different targets.

While the first version of this framework was built on top of the scientific computing language Scilab, the new, second
version now is based on Python.

**Please note:** The library currently under development and is its interface / API is considered experimental. Error messages might be missing, and some functions might be renamed or re-designed in the future. Further, up to now, simulation is limited to discrete-time systems and fixed-step simulation of continuous systems as the main target is real time simulation. Advanced continuous ODE-integrators, zero-crossings, etc. are missing so far.

The features implemented so far include:

- basic signal processing: transfer functions, rate limiters, different signal sources, ...
- control structures acting on subsystems: loops, triggered systems (if statements),
- state machines implemented in form of a set of subsystems one of which is active at a time,
- a simulator to execute models inside Python/Numpy (through code generation and just-in-time compilation thanks to [cppyy](https://cppyy.readthedocs.io/en/latest/),
- code generation and templates for code export: generic command-line executable, HTML/Javascript, MATLAB/Simulink.

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

Herein, a signal variable z is introduced that is combined with the system input u. The resulting intermediate variable x is then delayed and assigned to z closing the feedback loop. The delay has an initial value z[0] = 2.0.

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

## Algebraic loops

Watch out for algebraic loops - currently they are not automatically detected in any case! This will change soon.

## Targets for code generation

In the most simple form, the generated source code can simply be copy & pasted into the user's project. However, in addition target templates can be specified to automatically generate libraries or executables for various targets (e.g., a command line program, a library for the web, ...). 

Targets are combined in the 'openrtdynamics2.targets' sub-module.

### Minimal target

This is a minimal target to export generic c++ code that can be used in existing code ('TargetCppMinimal').

### Basic executable

To generate a basic command line executable that performs multiple simulation steps in a loop this target can be used ('TargetCppMain'). 

### Web Assembly

To export systems to a web (HTML) environment, the Web Assembly target can be used ('TargetCppWASM'). The system can be integrated into custom JavaScript code. Further, a JavaScript library is provided with which a simulation environment can be integrated into existing html-pages.

<img width="851" alt="HTMLexport" src="https://user-images.githubusercontent.com/4620523/121796863-81935880-cc1c-11eb-8da6-033d5c7baed0.png">

Consider, e.g., [pandemic_control_openloop.html](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/pandemic_control_openloop.html) and [pandemic_control.ipynb](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/pandemic_control.ipynb)

NOTE: If there is an unconnected input, the html export fails to run.

### Simulink

Systems can be exported and integrated into Simulink diagrams using the Simulink s-function target ('TargetCppSimulinkSFunction'). You might consider the example given in [Simulink s-function demo](https://github.com/OpenRTDynamics/openrtdynamics2/tree/master/examples/Simulink_sfunction_target) which includes a python notebook to generate code and a Simulink diagram the code can be executed with.

![simulink s-function](https://user-images.githubusercontent.com/4620523/121796812-1fd2ee80-cc1c-11eb-9f1b-8b7f756f0ab8.png)


### Linux real-time

Using this target, ('TargetLinuxRealtime'), code for Linux can be generated that is executed in real-time. Herein, the sampling time can be controlled by the system. Two modes are available: A soft real-time mode, which does not required special permissions to run. In the second mode, the scheduling policy of the process is changed to FIFO-mode using the Linux system call 'sched_setscheduler'. This requires special permissions (e.g., root) to run.

[Example](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/real-time/real-Time_linux.ipynb)

Please see https://wiki.linuxfoundation.org/realtime/start for further details

### Ideas for targets to come:
- real-time targets for Linux rt-preempt, Arduino and similar micro-controllers, ... (contributions are welcome)


## Tracing and debugging

Execution flows especially involving subsystems and state machines might get complex with increasing diagram complexity. Therefore, the execution flow (i.e., which subsystem is called when) can be traced. Currently, this is printf-based, however, also a visualization with timing diagrams might be feasible to implement.  

[Tracing and debugging](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/tracing_and_debugging.ipynb)

## Custom code

Sensors, actuators, means of communication, external libraries, and any other kind of functionality that provides a c/c++ interface can be embedded into custom blocks.  Custom (c++) code can be implemented into diagrams in form of user-provided c++ classes. See [Custom code](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/custom_cpp_code.ipynb) for examples and documentation.

## Custom targets

Code generation targets can be implemented by the user.

Please consider [custom target example](https://github.com/OpenRTDynamics/openrtdynamics2/blob/master/examples/custom_target.ipynb) for further information.

## Missing pieces

These lists might be considered as a list of things to do.

### Base framework

- Accidentally introduced algebraic loops are not handled well. Here, an error message is needed. Further, there are some cases in combination with subsystems where the handling of algebraic loops is too conservative meaning the compiler fails though there is not a real algebraic loop.
- A better framework for tracing and debugging, e.g., timing diagrams. Currently, this is printf-based. 
- vectorial/matrix signals are not implemented; the package Eigen might be used therefor.
- ability to yield exceptions that indicate errors in the computation 

- signals directly passed from the input to the output of a system causes fail code compilation. A workaround is to introduce a dummy computation, e.g., output = 1 * input
- In case there is a common name among the input and outputs of a system, compilation fails.

## Graphical user interface

- Introduce an online-editor, e.g., using [React Diagrams](https://github.com/projectstorm/react-diagrams).

## Background

Starting in 2008, OpenRTDynamics has been developed due to the lack of a suitable open-source alternative to the famous and powerful modelling tool Simulink (Mathworks). Within the years, the framework has evolved and applied in medical engineering research. The language was based on the scientific programming language [Scilab](scilab.org). The models are executed by a real-time capable interpreter.

OpenRTDynamics 2 is a re-implementation for the popular Python language. Further, the former interpreter is replaced by code generation. Finally, some concepts which had shortcomings in the old version are improved as Python introduces a bigger amount of flexibility.
