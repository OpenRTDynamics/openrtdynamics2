from . import lang as dy
from . import py_execute as dyexe
import openrtdynamics2.targets as tg

import functools


def ORTDtoNumpy(outputs_in_hash_array = False, custom_simulator_loop = None, **kwargs_decorator):
    """
    Function decorator: autoconversion of systems in the OpenRTDynamics framework to functions that do batch processing using numpy in- and output arrays

    The parameters to this decorator are passed to the wrapped function.

    Examples
    --------

        @ORTDtoNumpy()
        def fn1( a, b ):
            # this is OpenRTDynamics code
            
            c = a + b
            d = a * b
            
            return c, d

        c, d = fn1(1.5, 2.5)
        


        @ORTDtoNumpy(p=2)   # p=2 is fixed and will be compiled into
        def fn2( a, b, c : dy.SignalUserTemplate, d : dy.SignalUserTemplate, p ):
            # parameters annotated with dy.SignalUserTemplate will be treated as signals
            
            r = a + 10*b + 100*c + 1000*d + 10000*p
            return r
            
        r = fn2(1, 2, c=3, d=4)  # p cannot be specified here anymore as it is fixed

    """
    

    # helper fn
    def compile_system(func, kwargs, input_signal_names_p, input_signal_names):
        """
            compile the system that is defined by a given function
            
            func                 - the function that describes the system
            kwargs               - constant parameters to the function (no signals)
            input_signal_names_p - names of the input signals that are passed via position dependent parameters (the order is important)
            input_signal_names   - names of the input signals that are passed via named parameters
            
        """

        # put ORTD-code and define the schematic
        dy.clear()
        system = dy.enter_system()

        input_signals = []

        for input_name in input_signal_names_p:

            # create a new system input
            system_input = dy.system_input( dy.DataTypeFloat64(1), name=input_name )
            input_signals.append( system_input  )
            
        kwargs_signals = {}
        for input_name in input_signal_names:
            
            system_input = dy.system_input( dy.DataTypeFloat64(1), name=input_name )
            kwargs_signals[ input_name ] = system_input

        # run function to build system connections
        ret = func( *input_signals, **{ **kwargs_signals , **kwargs } )

        if type(ret) == tuple:
            output_signals = ret
        else:
            output_signals = [ret]

        # create outputs
        output_signal_counter = 1
        output_signal_names = []

        for output_signal in output_signals:
            output_signal_name = 'output_' + str(output_signal_counter)

            dy.append_output(output_signal, output_signal_name)

            output_signal_names.append( output_signal_name )
            output_signal_counter += 1

        output_signal_names = output_signal_names

        # generate c++ code
        code_gen_results = dy.generate_code(template=tg.TargetCppMinimal(enable_tracing=False))    

        # run c++ compiler
        compiled_system = dyexe.CompiledCode(code_gen_results) 
        
        return compiled_system, output_signal_names, code_gen_results

        
    def inner(func):

        @functools.wraps(func)
        def ORTDtoNumpy_inner(*args, **kwargs):

            #
            # check if the system is already compiled, if not do so
            #

            # print('fixed parameters', ORTDtoNumpy_inner.kwargs_decorator)
            
            
            if not ORTDtoNumpy_inner.is_compiled:

                #
                ORTDtoNumpy_inner.input_signal_names = []

                # find the function parameters that are annotated being ORTD-signals
                # and add these signals to the list of input signals
                for par_name, ann in func.__annotations__.items():

                    if ann is dy.SignalUserTemplate:
                        # print("ORTD input signal detected: ", par_name)

                        ORTDtoNumpy_inner.input_signal_names.append(par_name)

                    else:
                        raise BaseException('parameters that do not describe a ORTD-signal are not supported')


                # collect the position depended function parameters and add them as ORTD-signals
                input_signal_counter = 1
                ORTDtoNumpy_inner.input_signal_names_p = []

                for a in args:

                    ORTDtoNumpy_inner.input_signal_names_p.append('input_' + str(input_signal_counter))
                    input_signal_counter += 1


                # compile the system described by the function
                ORTDtoNumpy_inner.compiled_system, ORTDtoNumpy_inner.output_signal_names, ORTDtoNumpy_inner.code_gen_results = compile_system(func, ORTDtoNumpy_inner.kwargs_decorator, ORTDtoNumpy_inner.input_signal_names_p, ORTDtoNumpy_inner.input_signal_names)
                ORTDtoNumpy_inner.is_compiled = True


            #
            # Create an instance of the system and run the simulation
            #

            # compiled system: self.compiled_system

            ORTDtoNumpy_inner.simulation_instance = dyexe.SystemInstance(ORTDtoNumpy_inner.compiled_system)

            # collect input data
            input_data = {}

            # input data from parameters that have been annotated as ORTD signals
            for k, data in kwargs.items():

                input_data[ k ] = data

            # input data from position dependent parameters
            input_signal_counter = 1

            if len(args) != len(ORTDtoNumpy_inner.input_signal_names_p):
                raise BaseException('insufficient position based arguments')

            for a in args:

                input_data[ 'input_' + str(input_signal_counter) ] = a            
                input_signal_counter += 1

            #
            # run the simulation
            #

            # ORTDtoNumpy_inner.kwargs_decorator
            if ORTDtoNumpy_inner.custom_simulator_loop is None:
                sim_results = dyexe.run_batch_simulation(ORTDtoNumpy_inner.simulation_instance, input_data )
            else:
                # run the user-provided simulation loop
                sim_results = ORTDtoNumpy_inner.custom_simulator_loop(ORTDtoNumpy_inner.simulation_instance, input_data )


            #
            # return the results in the desired format
            #

            if ORTDtoNumpy_inner.outputs_in_hash_array:

                return sim_results

            elif len(ORTDtoNumpy_inner.output_signal_names) > 1:

                # form a tuple used to return the computed data
                return_value_in_tuple_form = ()

                for osn in ORTDtoNumpy_inner.output_signal_names:
                    # add output named osn            
                    return_value_in_tuple_form += ( sim_results[osn] , )

                return return_value_in_tuple_form

            else:

                # only return a single array of data

                for k, v in sim_results.items():
                    # return the only value inside sim_results
                    return v

        #
        # 'member vars' of class instance 'ORTDtoNumpy_inner' (which is a python function used as a class)
        #
        
        ORTDtoNumpy_inner.kwargs_decorator      = kwargs_decorator
        ORTDtoNumpy_inner.custom_simulator_loop = custom_simulator_loop
        ORTDtoNumpy_inner.outputs_in_hash_array = outputs_in_hash_array
        
        ORTDtoNumpy_inner.is_compiled           = False # is the system that is defined by the function already compiled?     
        ORTDtoNumpy_inner.code_gen_results      = None
        ORTDtoNumpy_inner.compiled_system       = None

        # signal names for in- and output
        ORTDtoNumpy_inner.output_signal_names   = None
        ORTDtoNumpy_inner.input_signal_names_p  = None  # autogenerated input signal names based on position dependent parameters 
        ORTDtoNumpy_inner.input_signal_names    = None  # input signal names read from self.func.__annotations__
        
        ORTDtoNumpy_inner.original_function     = func

        return ORTDtoNumpy_inner

    return inner

        
