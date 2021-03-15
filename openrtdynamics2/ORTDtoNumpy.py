
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

        # put ORTD-code and define the schematic
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
        
        # generate c++ code
        self.code_gen_results = dy.generate_code(template=dy.TargetRawCpp(enable_tracing=False))    
    
        # run c++ compiler
        self.compiled_system = dyexe.CompiledCode(self.code_gen_results) 




    def __call__(self, *args, **kwargs):
                
        #
        # check if the system is already compiled, if not do so
        #
        
        
        if not self.is_compiled:
            
            #
            input_signal_names = []
            
            # find the function parameters that are annotated being ORTD-signals
            # and add these signals to the list of input signals
            for par_name, ann in self.func.__annotations__.items():
                
                if ann is dy.SignalUserTemplate:
                    # print("ORTD input signal detected: ", par_name)
                    
                    input_signal_names.append(par_name)
                    
                else:
                    raise BaseException('parameters that do not describe a ORTD-signal are not supported')
                    
                
            # collect the position depended function parameters and add them as ORTD-signals
            input_signal_counter = 1           
            
            for a in args:
                
                # print( repr(a), a )
                
                input_signal_names.append('input_' + str(input_signal_counter))
                input_signal_counter += 1
                
            #   
            self.input_signal_names = input_signal_names
            
            # compile the system described by the function
            self.compile_system(input_signal_names)
            self.is_compiled = True
        
        
        #
        # Create an instance of the system and run the simulation
        #
        
        # compiled system: self.compiled_system
        
        simulation_instance = dyexe.SystemInstance(self.compiled_system)
        
        
        # collect input data
        input_data = {}

        
        # input data from parameters that have been annotated as ORTD signals
        for k, data in kwargs.items():
            input_data[ k ] = data
            

        
        # input data from position dependent parameters
        input_signal_counter = 1
        
        for a in args:
            
            input_data[ 'input_' + str(input_signal_counter) ] = a            
            input_signal_counter += 1

                
                
                
                
        # run the simulation
        sim_results = dyexe.run_batch_simulation(simulation_instance, input_data )
        
        # return the results in the desired format
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


        


