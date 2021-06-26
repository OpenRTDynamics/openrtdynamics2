import numpy as np
from typing import Dict, List
from .manifest_import import get_all_inputs
system_instance_counter = 0

#__all__ = []
#__all__ = ['show_required_inputs', 'run_batch_simulation', 'SystemInstance', 'CompiledCode']





def fill_default_input_values( manifest, inputs ):

    ret = get_all_inputs( manifest, only_inputs_with_default_values = True )

    for k, v in ret.items():
        setattr(inputs, k, v['properties']['default_value'])




class CompiledCode:
    
    def __init__(self, code_gen_results):
        """
            Compile a system so that it can be instanciated and, hence, executed 
        
            code_gen_results  - the returned results of dy.generate_code

            Note: internally the c++ interpreter Cling C++ interpreter is used
            that is interfaced by Python via https://pypi.org/project/cppyy/ .
        """
    
        import cppyy

        global system_instance_counter

        #
        # Note:
        #
        # Issue: https://bitbucket.org/wlav/cppyy/issues/295/q-reset-interpreter-or-multiple-instances
        #
        # Symbols once create in the cppyy.glb namespace cannot be deleted or overwritten.
        # Therefore, all code is wrapped into a namespace with a unique name that involves a
        # counter that increases for each call of cppyy.cppdef(src). Even if an instance of CompiledCode
        # is destructed, the compiled c++ module remains in the cppyy.glb namespace, hence, over time
        # symbols are accumulated. Hence, this is a memory leak. I do not know how to solve this.
        #

        ortd_auto_namespace_id = system_instance_counter
        system_instance_counter = system_instance_counter + 1
        
        algorithm_sourcecode, manifest = code_gen_results['algorithm_sourcecode'], code_gen_results['manifest']        
        self._manifest = manifest        

        # wrap all classes into a unique namespace
        src = 'namespace ' + 'ortd_system_ns' + str(ortd_auto_namespace_id) + '{\n' + algorithm_sourcecode + '\n}'

        # send sourcecode to jit-compiler
        cppyy.cppdef(src)

        # load module and extract the main class 'simulation'
        cpp_class_of_system = getattr(cppyy.gbl, 'ortd_system_ns' + str(ortd_auto_namespace_id) ).simulation

        # store
        self._cpp_class_of_system = cpp_class_of_system

    @property
    def system_class(self):
        return self._cpp_class_of_system
        
    @property
    def manifest(self):
        return self._manifest
        




class SystemInstance:
    
    def __init__(self, compiled_code : CompiledCode):
        """
            Instantiate a system so that it can be executed 
        
            compiled_code   - an instance of CompiledCode
        """

        self._compiled_code = compiled_code

        system_class = compiled_code.system_class


        # create an instance of the system
        self._sim = system_class()

        # create instances for the in- and output signals        
        self.inputs = system_class.Inputs()
        self.outputs = system_class.Outputs()
        
        fill_default_input_values( compiled_code.manifest, self.inputs )
        
        
    def reset_states(self):
        """
            reset all internal states of the system and all subsystems
        """
        self._sim.step( self.outputs, self.inputs, 0, False, True )

    def calculate_outputs(self):
        self._sim.step( self.outputs, self.inputs, 1, False, False )
        return self.outputs

    def update_states(self):
        self._sim.step( self.outputs, self.inputs, 0, True, False )

    def single_step(self):
        """
            perform one step and return the system outputs

            Please note: the inputs must be via the member variable inputs before.
        """
        res = self.calculate_outputs()
        self.update_states()

        return res

        
    @property
    def instance(self):
        return self._sim
    
    @property
    def manifest(self):
        return self._compiled_code.manifest
        
        
        

def run_batch_simulation(system_instance : SystemInstance, input_data, N=None, output_keys=None, reset_system=True ):
    """
        Run a simulation
        
        system_instance : SystemInstance - the instance of the system to simulate
        input_data                       - hash array containing the input data stored in arrays
        N                                - optional: the number of steps to simulate; when None, N is determined
                                           automatically given the input data.
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
    
    # detect single values in input_data which will be treated as constants
    input_data_without_const_values = {}
    for k in input_data.keys():

        val = input_data[k]

        if hasattr(inputs, k):
            if type(val) == float or type(val) == int or np.size( val ) == 1:
                setattr(inputs, k, val)
                # print('set const value', val, ' for ', k)
            else:
                input_data_without_const_values[k] = val

    # determine the number of samples to simulate: find minimal N from given data
    if N is None:

        Nset = [ np.size(data) for k, data in input_data_without_const_values.items() ]

        if len(Nset) == 0:
            N = 1
        else:
            N = np.min(Nset)

        # print('determined N ', N)


    # allocate memory for output signals
    storage = { k : np.zeros(N) for k in output_keys }
                
    # reset system 
    if reset_system:
        system_instance.reset_states()
    
    # start simulation
    for i in range(0,N):
        
        for k in input_data_without_const_values.keys():
            val = input_data_without_const_values[k][i]
            setattr(inputs, k, val)

        outputs = system_instance.calculate_outputs()
        system_instance.update_states()

        for k in output_keys:
            val = getattr(outputs, k)
            storage[k][i] = val

    return storage


# def show_required_inputs(testsim):
#     """
#         Print a table containing all input signals as required by the simulator functions
#         of the implemented system.

#         system_instance : SystemInstance - the instance of the system
#     """

#     from prettytable import PrettyTable

#     s_o_1 = testsim.manifest['io']['inputs']['calculate_output']['names']
#     s_u = testsim.manifest['io']['inputs']['state_update']['names']
#     s_r = testsim.manifest['io']['inputs']['reset']['names']

#     all_signals = list(set(s_o_1 + s_u + s_r) )

#     table_rows = []
#     for k in all_signals:

#         o_1, u, r = '', '', ''

#         if k in s_o_1:
#             o_1 = 'X'

#         if k in s_u:
#             u = 'X'

#         if k in s_r:
#             r = 'X'

#         row = [ k, o_1, u, r ]

#         table_rows.append(row)


#     x = PrettyTable()
#     x.field_names = ["input signal,  needed for -->", "calc. outputs", "update", "reset"]

#     x.add_rows(table_rows)

#     print(x)
    





