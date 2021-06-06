from .lang.diagram_core.code_build_commands import *
from .lang.diagram_core.system_manifest import *
from .lang.diagram_core import diagram_compiler
from .lang.libraries import *
from .manifest_import import get_all_inputs, get_all_outputs

import json
import os
import string
import subprocess
from pathlib import Path


def generate_algorithm_code( 
        compile_results, 
        enable_tracing=False, 
        included_systems={}, 
        list_of_code_sources = {}
    ):
    """
        generate code for the given compile result

        compile_results    - the compilation results of the a system
        enable_tracing     - include debuging
        included_systems   - unused so far
        list_of_code_sources  - list of strings containing code to include
    """

    main_command = compile_results.command_to_execute

    algorithm_code = ''

    # enable tracing for all execution commands
    if enable_tracing:
        # TODO: instead of putting True create an obj with a tracing infrastructure. So far printf is used automatically
        main_command.set_tracing_infrastructure(True)

    # concatenate the custom code to include
    if list_of_code_sources is not None:
        for identifier, code_source in list_of_code_sources.items():

            if 'code' in code_source:
                algorithm_code += '// custom code\n' + code_source['code'] + '\n// end of custom code\n\n'
            else:
                raise BaseException('not implemented')

    # combine (concatenate) the code from the library entries
    for include in included_systems:
        algorithm_code += include.sourceCode

    # build the code for the implementation
    main_command.generate_code_init('c++')
    algorithm_code += main_command.generate_code('c++', 'code')
    main_command.generate_code_destruct('c++')

    # the manifest containts meta-information about the simulation and its interface
    # i.e. input and output signals names and datatypes
    manifest = compile_results.manifest # .export_json()

    return manifest, algorithm_code





class TargetTemplate:
    """
        template for a custom target
    """

    def __init__(self, enable_tracing=False ):

        # those are set via set_compile_results after a system is compiled
        self.compileResults = None
        self.main_command = None
        self._list_of_code_sources = {}
        
        self.files = None
        self.folder = None

        #
        self._algorithm_code = None

        # list of systems to include
        self._included_systems = []

        self._enable_tracing = enable_tracing

#    def set_compile_results(self, compile_results : CompileResults ):
    def set_compile_results(self, compile_results ):
        
        self.compileResults = compile_results
        self.main_command = compile_results.command_to_execute

#    def include_systems(self, system : SystemLibraryEntry):
    def include_systems(self, system ):
        
        self._included_systems = system

    def add_code_to_include(self, list_of_code_sources = {}):
        
        self._list_of_code_sources = { **self._list_of_code_sources, **list_of_code_sources }

    def get_algorithm_code(self):
        """
            Return only the code that implement the system and all sub systems
        """
        return self._algorithm_code



    def code_gen(self):

        # generate code for the algorithm
        self.manifest, self._algorithm_code = generate_algorithm_code(
            self.compileResults, 
            self._enable_tracing, 
            self._included_systems, 
            self._list_of_code_sources
        )

        self.manifest_structure = self.manifest.export_json()

        self.files = {}
        self.files['simulation_manifest.json'] = json.dumps( self.manifest_structure , indent=4 )
        
        # embed algorithm source code into a template
        sourcecode = self._algorithm_code
        

        # return
        return {
            'files'                : self.files,
            'sourcecode'           : sourcecode, # remove this in favor of 'files'
            'manifest'             : self.manifest_structure,
            'algorithm_sourcecode' : self._algorithm_code }

    def write_code(self, folder):

        self.folder = folder
            
        for fname, content in self.files.items():
            fullname = os.path.join( folder, fname )
            
            print('writing file', fullname)
            
            with open( fullname, 'w') as outfile: 
                
                outfile.write( content )
                

    def build(self):
        pass

    def run(self):
        pass



#
#
#




class TargetCppMinimal(TargetTemplate):
    """
        minimal c++ export
    """

    def __init__(self, enable_tracing=False ):
        """
        i_max is the number of simulated steps.
        """
        
        TargetTemplate.__init__(self, enable_tracing)

    def build(self):
        print("Build not supported")
        
        
    def code_gen(self):
        # build code of system
        res = TargetTemplate.code_gen(self)
        
        # get the system manifest and c++ class name
        m = res['manifest']
        simulation_name = m['api_name']
        
        # headers
        headers = '#include <stdio.h>\n'
        
        
        
        #
        # build main.cpp
        #
        
        main_cpp = headers + '\n' + res['algorithm_sourcecode'] + '\n'
        
        self.files[simulation_name + '.cpp'] = main_cpp
        
        # return
        return res






class TargetCppMain(TargetTemplate):
    """
        generate a simple main.cpp program

        i_max is the number of simulated steps.
    """

    def __init__(self, i_max = 20, enable_tracing=False ):
        """
        i_max is the number of simulated steps.
        """
        
        TargetTemplate.__init__(self, enable_tracing)
        self.i_max = i_max

    def build(self):
        
        main_cpp    = os.path.join( self.folder, 'main.cpp' )
        main_binary = os.path.join( self.folder, 'main' )
        build_command = "c++ " + main_cpp + " -o " + main_binary
        
        print("Running build command: " + build_command)
        
        return_code = os.system(build_command)
        print( "Compilation result: ", return_code )
        
        
    def code_gen(self):
        # build code of system
        res = TargetTemplate.code_gen(self)
        
        # get the system manifest and c++ class name
        m = res['manifest']
        simulation_name = m['api_name']
        
        # headers
        headers = '#include <stdio.h>\n'
        
        # define structs for I/O
        variables = simulation_name + ' system_instance;\n' + simulation_name + '::Inputs inputs;\n' + simulation_name + '::Outputs outputs;\n'
        
        
        #
        # create a list of the system inputs
        #
        
        inputs = get_all_inputs( m, only_inputs_with_default_values = True )

        fill_input_values = ''
        for input_name, v in inputs.items():
            
            print(input_name, v['properties']['default_value'], v['cpptype'])
            
            fill_input_values += 'inputs.' + input_name + ' = ' + str( v['properties']['default_value'] ) + ';\n' #, v['cpptype']

        #
        # create a list of the system outputs and a printf to print the data
        #
        
        outputs = get_all_outputs( m )

        printf_patterns   = []
        printf_parameters = []
        
        for output_name, v in outputs.items():
            printf_patterns.append( v['printf_pattern'] )
            printf_parameters.append( 'outputs.' + output_name )
            
        
        outputs_printf = 'printf("' + ' '.join(printf_patterns) + '\\n", ' + ', '.join(printf_parameters) + ');\n'
        
        #
        # template code
        #
        
        main_fn = """
int main () {
""" + indent(variables, '    ') + """
    
    // set const inputs
""" + indent(fill_input_values, '    ') + """
    
    // reset system
    system_instance.step( outputs, inputs, false, false, true );
    
""" + indent('int i_max = ' + str(self.i_max) + ';\n', '    ') + """
    
    for (int i = 0; i < i_max; ++i) {
        
        // calculate outputs
        system_instance.step( outputs, inputs, true, false, false );
        
        // update states
        system_instance.step( outputs, inputs, false, true, false );
    
        // print outputs
""" + indent(outputs_printf, '        ') + """
    } 
    
    return 0;
}
        
        """
        
        #
        # build main.cpp
        #
        
        main_cpp = headers + '\n' + res['algorithm_sourcecode'] + '\n' + main_fn
        
        self.files['main.cpp'] = main_cpp
        
        # return
        return res




















class TargetCppWASM(TargetTemplate):
    """
        Export to Web Assembly using the c++ compiler emscripten 
        
        https://emscripten.org/
    """

    def __init__(self, enable_tracing=False ):
        
        TargetTemplate.__init__(self, enable_tracing)

        
    def build(self):

        build_command = 'emcc --bind -s MODULARIZE=1 -s EXPORT_NAME="ORTD_simulator" '  + os.path.join(self.folder, "main.cpp") + " -O2 -s -o " + os.path.join( self.folder , "main.js" )
        print("Running compiler: " + build_command)

        return_code = os.system(build_command)
        print( "Compilation result: ", return_code )

        
        
    def code_gen(self):
        # build code of system
        res = TargetTemplate.code_gen(self)
        
        # get the system manifest and c++ class name
        m = res['manifest']
        simulation_name = m['api_name']
        
        # headers
        headers = """        
#include <math.h>
#include <stdio.h>
#include <emscripten/bind.h>

using namespace emscripten;
        """

        def generate_binding_code(system_cpp_class_name, struct_name : str, names ):

            lines = ''
            lines += 'value_object<' + system_cpp_class_name + '::' + struct_name + '>("' + system_cpp_class_name + '__' + struct_name + '")\n'

            for name in names:

                lines += '.field("' + name + '", &' + system_cpp_class_name + '::' + struct_name + '::' + name + ')\n'

            lines += ';\n\n'


            return lines        
        
        # define structs for I/O
        variables = simulation_name + ' system_instance;\n' + simulation_name + '::Inputs inputs;\n' + simulation_name + '::Outputs outputs;\n'
        
        
        #
        # create binding code to export the c++ API to Java Script
        #
        
        binding_code = """


// Binding code
EMSCRIPTEN_BINDINGS(my_class_example) {
  class_<$simulation_name>("$simulation_name")
    .constructor<>()
    .function("resetStates", &$simulation_name::resetStates__)
    .function("calcResults_1", &$simulation_name::calcResults_1__)
    .function("updateStates", &$simulation_name::updateStates__)
    .function("step", &$simulation_name::step)
    ;

        
"""
        
        binding_code = string.Template(binding_code).safe_substitute( simulation_name = simulation_name )
        
        binding_code += generate_binding_code(
            
            simulation_name, 
            'Inputs',
            
            get_all_inputs( 
                m,
                only_inputs_with_default_values    = False, 
                return_inputs_to_update_states     = True,
                return_inputs_to_calculate_outputs = True,
                return_inputs_to_reset_states      = True
            )
        )
        
        binding_code += generate_binding_code(
            
            simulation_name, 
            'Outputs',
            
            get_all_outputs( 
                m
            )
        )
        
        #
        
        binding_code += generate_binding_code(
            
            simulation_name, 
            'Inputs_' + m['api_functions']['calculate_output'],
            
            get_all_inputs( 
                m,
                only_inputs_with_default_values    = False, 
                return_inputs_to_update_states     = False,
                return_inputs_to_calculate_outputs = True,
                return_inputs_to_reset_states      = False
            )
        )

        binding_code += generate_binding_code(
            
            simulation_name, 
            'Outputs_' + m['api_functions']['calculate_output'],
            
            get_all_outputs( 
                m,
                return_inputs_to_update_states     = False,
                return_inputs_to_calculate_outputs = True,
                return_inputs_to_reset_states      = False
            )
        )

        
        
        binding_code += generate_binding_code(

            simulation_name, 
            'Inputs_' + m['api_functions']['state_update'],
            
            get_all_inputs( 
                m,
                only_inputs_with_default_values    = False, 
                return_inputs_to_update_states     = True,
                return_inputs_to_calculate_outputs = False,
                return_inputs_to_reset_states      = False
            )
        )

        binding_code += generate_binding_code(

            simulation_name, 
            'Outputs_' + m['api_functions']['state_update'],
            
            get_all_outputs( 
                m,
                return_inputs_to_update_states     = True,
                return_inputs_to_calculate_outputs = False,
                return_inputs_to_reset_states      = False
            )
        )




        binding_code += generate_binding_code(

            simulation_name, 
            'Inputs_' + m['api_functions']['reset'],
            
            get_all_inputs( 
                m,
                return_inputs_to_update_states     = False,
                return_inputs_to_calculate_outputs = False,
                return_inputs_to_reset_states      = True
            )
        )
        
        binding_code += generate_binding_code(

            simulation_name, 
            'Outputs_' + m['api_functions']['reset'],
            
            get_all_outputs( 
                m,
                return_inputs_to_update_states     = False,
                return_inputs_to_calculate_outputs = False,
                return_inputs_to_reset_states      = True
            )
        )

        binding_code += '\n}\n'
        
        #
        # template code
        #
        
        main_fn = binding_code
        
        #
        # build main.cpp
        #
        
        main_cpp = headers + '\n' + res['algorithm_sourcecode'] + '\n' + main_fn
        
        self.files['main.cpp'] = main_cpp
        
        # return
        return res



