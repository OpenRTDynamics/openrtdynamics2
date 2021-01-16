import cppyy
import numpy as np

def fill_default_input_values( manifest, inputs ):

    manifest_in_o = manifest['io']['inputs']['calculate_output']
    manifest_in_u = manifest['io']['inputs']['state_update']

    def fill_in(inputs, manifest_in):

        for i in range(len(manifest_in['names'])):

            k = manifest_in['names'][i]

            if not 'properties' in manifest_in:
                break

            properties = manifest_in['properties'][i]

            if not 'default_value' in properties:
                break

            default_val = properties['default_value']

            setattr(inputs, k, default_val)


    fill_in(inputs, manifest_in=manifest_in_o)
    fill_in(inputs, manifest_in=manifest_in_u)


class SystemInstance:
    
    def __init__(self, code_gen_results):
        """
            Instantiate a system so that it can be executed 
        
            code_gen_results  - the returned results of dy.generate_code

            Note: internally the c++ interpreter Cling C++ interpreter is used
            that is interfaced by Python via https://pypi.org/project/cppyy/ .
        """
        
        algorithm_sourcecode, manifest = code_gen_results['algorithm_sourcecode'], code_gen_results['manifest']        
        
        # TODO: wrap source code into namespace
        cppyy.cppdef(algorithm_sourcecode)
        from cppyy.gbl import simulation
        
        self._sim = simulation()
        self._manifest = manifest
        
        self.inputs = simulation.Inputs()
        self.outputs = simulation.Outputs()
        
        fill_default_input_values( self._manifest, self.inputs )
        
        
    def reset_states(self):
        self._sim.step( self.outputs, self.inputs, 0, False, True )

    def calculate_outputs(self):
        self._sim.step( self.outputs, self.inputs, 1, False, False )
        return self.outputs

    def update_states(self):
        self._sim.step( self.outputs, self.inputs, 0, True, False )
        
    @property
    def instance(self):
        return self._sim
    
    @property
    def manifest(self):
        return self._manifest
        
        
        

def run_batch_simulation(system_instance, input_data, N, output_keys=None, reset_system=True ):
    """
        Run a simulation
        
        system_instance : SystemInstance - the instance of the system to simulate
        input_data                       - hash array containing the input data stored in arrays
        N                                - the number of steps to simulate
        output_keys                      - a list of output signals of which the traces are stored
        reset_system                     - reset the system before starting the simulation (if false, a
                                           previous simulation can be continued)
        
    
        Example usage:
        --------------
    
        testsim = SystemInstance(algorithm_sourcecode, manifest)
    
        # 1) Get all output signals
        
        N=3000
        input_data = {'velocity' : 2*np.ones(N), 'time_scale' : 7 }
        sim_results_full = run_batch_simulation(testsim, input_data, N )
        
        # 2) Get only a subset of the output signals
        
        sim_results = run_batch_simulation(testsim, input_data, N,  output_keys=['x', 'y', 'steering'] )

    """
    
    # get memory for input signals 
    inputs = system_instance.inputs
    
    #
    if output_keys is None:
        output_keys = system_instance.manifest['io']['outputs']['calculate_output']['names']
    
    # allocate memory for output signals
    storage = { k : np.zeros(N) for k in output_keys }

    # detect single values in input_data which will be treated as constants
    input_data_without_const_values = {}
    for k in input_data.keys():

        val = input_data[k]

        if hasattr(inputs, k):
            if type(val) == float or type(val) == int:
                setattr(inputs, k, val)
                print('set const value', val, ' for ', k)
            else:
                input_data_without_const_values[k] = val

                
    # reset system 
    if reset_system:
        system_instance.reset_states()
    
    # start simulation
    for i in range(1,N):
        
        for k in input_data_without_const_values.keys():
            val = input_data_without_const_values[k][i]
            setattr(inputs, k, val)

        outputs = system_instance.calculate_outputs()
        system_instance.update_states()

        for k in output_keys:
            val = getattr(outputs, k)
            storage[k][i] = val

    return storage


