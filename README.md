# OpenRTDynamics 2

-- Open Real-Time Dynamics 2 - A modelling framework for dynamic systems (http://openrtdynamics.github.io/)

OpenRTDynamics 2 is a framework to support implementing control systems, signals processing algorithms, and dynamic simulations. Provided is a python library for defining such systems and to generate code (c++) from them. Templates
can be used to adapt the generated code to different targets.

While the first version of this framework was build on top of the scientific computing language Scilab, the new, second
version now is based on Python.

Please note: in its current state, the library is considered experimental and the interface might be subjected to 
changes. Further, up to now it is limited to discrete-time systems - no continuous ODE-integrators.

The following features are implemented

- basic signal processing: transfer functions, rate limiters, different signal sources, ...
- subsystems: loops, triggered systems
- state machines implemented in form of a set of subsystems of which one is active at a time
- some code generation templates: generic printf-based command-line, web assemble (to run in models in Javascript) 

