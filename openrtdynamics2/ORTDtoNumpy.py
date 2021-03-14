
import functools
from . import lang as dy
from . import py_execute as dyexe



class ORTDtoNumpy:
    """
    Function decorator: autoconversion of systems in the OpenRTDynamics framework to functions that do batch processing using numpy in- and output arrays

    Examples
    --------

        @ORTDtoNumpy
        def test_fn1( a, b ):
            # this is OpenRTDynamics code
            
            c = a + b
            d = a * b
            
            return c, d

        c, d = test_fn1(1.5, 2.5)
        
    """
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        
        self.is_compiled = False
        
        self.code_gen_results    = None
        self.compiled_system     = None
        self.output_signal_names = None
        self.input_signal_names  = None
        
        
    def compile_system(self, input_signal_names):

        
        dy.clear()
        system = dy.enter_system()
        
        input_signals = []
        
        for input_name in input_signal_names:
            
            # create a new system input
            system_input = dy.system_input( dy.DataTypeFloat64(1), name=input_name )
            input_signals.append( system_input  )
        
        
        # run function to build system connections
        ret = self.func( *input_signals )
        
        if type(ret) == tuple:
            output_signals = ret
        else:
            output_signals = [ret]
        
        # create outputs
        output_signal_counter = 1
        output_signal_names = []
        
        for output_signal in output_signals:
            output_signal_name = 'output_' + str(output_signal_counter)
            
            dy.append_primay_ouput(output_signal, output_signal_name)
            
            
            output_signal_names.append( output_signal_name )
            output_signal_counter += 1
            
        self.output_signal_names = output_signal_names
        
            
        # generate code for Web Assembly (wasm), requires emcc (emscripten) to build
        self.code_gen_results = dy.generate_code(template=dy.TargetRawCpp(enable_tracing=False))    
    
        # run c++ compiler
        self.compiled_system = dyexe.CompiledCode(self.code_gen_results) 




    def __call__(self, *args, **kwargs):
                
        #
        # check if the system is already compiled, if not do so
        #
        
        
        if not self.is_compiled:
            
            input_signal_names = []
            input_signal_counter = 1
            
            for a in args:
                input_signal_names.append('input_' + str(input_signal_counter))
                input_signal_counter += 1
                
            

            for k, v in kwargs.items():
                # this is not implemented
                
                raise BaseException('Not implemented')
                # print(k, '-->', v)
                
                input_signal_names.append('input_' + str(input_signal_counter))
                input_signal_counter += 1
                
                
            self.input_signal_names = input_signal_names
            self.compile_system(input_signal_names)
        
            self.is_compiled = True
        
        
        #
        # Create an instance of the system and run the simulation
        #
        
        # compiled system: self.compiled_system
        
        simulation_instance = dyexe.SystemInstance(self.compiled_system)
        
        input_data = {}
        input_signal_counter = 1
        for a in args:
            
            input_data[ 'input_' + str(input_signal_counter) ] = a            
            input_signal_counter += 1

                
        sim_results = dyexe.run_batch_simulation(simulation_instance, input_data )
        
        if len(self.output_signal_names) > 1:
            
            # form a tuple used to return the computed data
            
            return_value_in_tuple_form = ()

            for osn in self.output_signal_names:
                # add output named osn            
                return_value_in_tuple_form += ( sim_results[osn] , )

            return return_value_in_tuple_form
        
        else:
            
            # only return a single array of data
            
            for k, v in sim_results.items():
                # return the only value inside sim_results
                return v


        
        

# @ORTDtoNumpy
# def distance_to_line_np( xs, ys, xe, ye, x_test, y_test ):
    
#     Delta_l, distance_s_to_projection = distance_to_line(xs, ys, xe, ye, x_test, y_test)
    
#     return Delta_l, distance_s_to_projection



# @ORTDtoNumpy
# def test_fn( a, b ):
    
#     c = a + b
#     d = a * b
    
#     return c, d


# @ORTDtoNumpy
# def test_fn2( a, b ):
    
#     c = a + b
    
#     return c


# @ORTDtoNumpy
# def test_fn2( u ):
    
#     y = dy.dtf_lowpass_1_order(u, 0.6)
    
#     return y
