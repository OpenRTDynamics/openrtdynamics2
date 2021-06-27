from .lang.diagram_core.code_build_commands import *
from .lang.diagram_core.system_manifest import *
from .lang.diagram_core import diagram_compiler
from .lang.libraries import *
from .manifest_import import get_all_inputs, get_all_outputs, show_inputs, show_outputs

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
        headers =  '#include <stdio.h>\n'
        headers += '#include <math.h>\n'
        
        
        
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
        headers =  '#include <stdio.h>\n'
        headers += '#include <math.h>\n'
        
        # define structures for I/O
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




#
# MATLAB/Simulink s-function target
#

class TargetCppSimulinkSFunction(TargetTemplate):
    """
        Target for MATLAB/Simulink s-functions
        
        sfun_name - a string describing the name of the s-function.
        
        A file 'sfun_name'.cpp will be generated that contains the code for the s-function.
        It can be compiled from the Matlab command line using the command
        
            mex 'sfun_name'.cpp
            
        Then, the compiled system can be interfaced via the s-function block in Simulink.
        The input-/output ports are enumerated as they are defined in the system implementation.
    """

    def __init__(self, enable_tracing=False, sfun_name : str = 'sfunction'):
        TargetTemplate.__init__(self, enable_tracing)
        self.sfun_name = sfun_name

    def code_gen(self):
        # build code of system        
        res = TargetTemplate.code_gen(self)
        
        # get the system manifest and c++ class name
        m = res['manifest']
        simulation_name = m['api_name']

        # filenames
        cpp_fname       = self.sfun_name + '.cpp'
        interface_fname = self.sfun_name + '_block_mask_commands.m'
        
        # headers
        headers =  '#include <stdio.h>\n'
        headers += '#include <math.h>\n'

        # define map c++ to simulink datatypes
        def datatypes_c_to_simulink( cpptype : str, what_index : int = 0 ):

            map_datatypes_c_to_simulink = {
                'double'     : ['SS_DOUBLE',  'real_T',     'InputRealPtrsType'],
                'real'       : ['SS_SINGLE',  ''],

                'int8_t'     : ['SS_INT8',    'int8_T',     'InputInt8PtrsType'],
                'uint8_t'    : ['SS_UINT8',   ''],
                'int16_t'    : ['SS_INT16',   'int16_T',    'InputInt16PtrsType'],
                'uint16_t'   : ['SS_UINT16',  ''],
                'int32_t'    : ['SS_INT32',   'int32_T',    'InputInt32PtrsType'],
                'uint32_t'   : ['SS_UINT32',  ''],

                'bool'       : ['SS_BOOLEAN', 'boolean_T',  'InputBooleanPtrsType']
            }

            if cpptype in map_datatypes_c_to_simulink: 
                return map_datatypes_c_to_simulink[cpptype][what_index]
            else:
                raise BaseException('Not implemented: datatype ' + cpptype + ' cannot be converted to a Simulink datatype' )

        
        # define structures for I/O
        io_variables_define = simulation_name + '::Inputs inputs;\n' + simulation_name + '::Outputs outputs;\n'

        #
        # create a list of all system inputs including those that are
        # not needed to run the system.
        #

        all_input_signals = m['io']['all_inputs_by_port_number']

        define_input_port_sizes     = ''
        define_input_port_datatypes = ''
        icon_drawing_commands       = '% copy and paste these commands into the field \'icon drawing commands\' of the block mask: \n'
        icon_drawing_commands      += '% right-click on block -> \'Mask\' -> \'Edit Mask\' -> \'Mask Editor\' -> \'Icons & Ports\'\n\n'
        number_of_inputs = len(all_input_signals)

        for port_number in range(0, number_of_inputs ):

            port_number_str      = str( port_number )
            signal_name          = all_input_signals[port_number]['name']
            signal_type          = all_input_signals[port_number]['cpptype']
            signal_simulink_type = datatypes_c_to_simulink(signal_type)

            define_input_port_sizes     += 'ssSetInputPortWidth(S, '    + port_number_str +', 1); // '+ signal_name  + '\n'
            define_input_port_datatypes += 'ssSetInputPortDataType(S, ' + port_number_str +', ' + signal_simulink_type + '); // ' + signal_name  + ' (' + signal_type + ')\n'
            icon_drawing_commands       += 'port_label(\'input\', '     + str(port_number + 1) + ', \'' + signal_name + '\')\n'


        #
        # create a list of all system inputs that are used 
        # (not all declared inputs might be used in the system)
        #
        
        inputs = get_all_inputs( m )

        get_s_inputs            = '' 
        fill_input_values       = ''
        
        for input_name, v in inputs.items():
            
            port_number     = v['port_number']
            port_number_str = str( port_number )

            simulink_c_type     = datatypes_c_to_simulink(  all_input_signals[port_number]['cpptype'], what_index=1  )
            simulink_c_ptr_type = datatypes_c_to_simulink(  all_input_signals[port_number]['cpptype'], what_index=2  )
            
            get_s_inputs            += simulink_c_ptr_type + ' uPtrs' + port_number_str + ' = (' + simulink_c_ptr_type + ') ssGetInputPortSignalPtrs(S,' + port_number_str + ');\n'
            fill_input_values       += 'inputs.' + input_name + ' = *uPtrs' + port_number_str + '[0];\n'

            
        #
        # create a list of the system inputs needed to compute the blocks outputs
        #
        
        inputs_for_block_outputs = get_all_inputs( 
            m, 
            return_inputs_to_calculate_outputs = True, 
            return_inputs_to_reset_states      = False,
            return_inputs_to_update_states     = False
        )
        
        get_s_inputs_for_model_outputs      = '' 
        fill_input_values_for_model_outputs = ''
        set_direct_feedthrough              = ''
        
        for input_name, v in inputs_for_block_outputs.items():
            
            port_number     = v['port_number']
            port_number_str = str( port_number )

            simulink_c_type     = datatypes_c_to_simulink(  all_input_signals[port_number]['cpptype'], what_index=1  )
            simulink_c_ptr_type = datatypes_c_to_simulink(  all_input_signals[port_number]['cpptype'], what_index=2  )

            get_s_inputs_for_model_outputs      += simulink_c_ptr_type + ' uPtrs' + port_number_str + ' = (' + simulink_c_ptr_type + ') ssGetInputPortSignalPtrs(S,' + port_number_str + ');\n'
            fill_input_values_for_model_outputs += 'inputs.' + input_name + ' = *uPtrs' + port_number_str + '[0];\n'
            set_direct_feedthrough              += 'ssSetInputPortDirectFeedThrough(S, ' + port_number_str + ', 1); // ' + input_name +  '\n'
       
        #
        # create a list of the system inputs needed to update the systems states
        #
        
        inputs_for_state_update = get_all_inputs( 
            m, 
            return_inputs_to_calculate_outputs = False, 
            return_inputs_to_reset_states      = False,
            return_inputs_to_update_states     = True
        )
        
        get_s_inputs_for_state_update      = '' 
        fill_input_values_for_state_update = ''
        
        for input_name, v in inputs_for_state_update.items():
            
            port_number     = v['port_number']
            port_number_str = str( port_number )

            simulink_c_type     = datatypes_c_to_simulink(  all_input_signals[port_number]['cpptype'], what_index=1  )
            simulink_c_ptr_type = datatypes_c_to_simulink(  all_input_signals[port_number]['cpptype'], what_index=2  )

            get_s_inputs_for_state_update      += simulink_c_ptr_type + ' uPtrs' + port_number_str + ' = (' + simulink_c_ptr_type + ') ssGetInputPortSignalPtrs(S,' + port_number_str + ');\n'
            fill_input_values_for_state_update += 'inputs.' + input_name + ' = *uPtrs' + port_number_str + '[0];\n'

            
        #
        # create a list of the system outputs
        #
        
        outputs = get_all_outputs( m )
        number_of_outputs = len(outputs)

        get_outputs                  = ''
        fill_output_values           = ''
        define_output_port_sizes     = ''
        define_output_port_datatypes = ''
        
        port_number = 0 # output port index for simulink, starting at 0
        for output_name, v in outputs.items():

            port_number_str = str( port_number )

            signal_type               = v['cpptype']
            signal_simulink_type      = datatypes_c_to_simulink(signal_type)
            simulink_c_type           = datatypes_c_to_simulink(signal_type, what_index=1)
            #simulink_c_ptr_type       = datatypes_c_to_simulink(signal_type, what_index=2)
            
            get_outputs              += simulink_c_type + ' *y' + port_number_str + ' = (' + simulink_c_type + ' *) ssGetOutputPortSignal(S, ' + port_number_str + ');\n'

            fill_output_values       += 'y' + port_number_str + '[0] = outputs.' + output_name + ';\n'
            define_output_port_sizes += 'ssSetOutputPortWidth(S, ' + port_number_str + ', 1); // ' + output_name + '\n'
            icon_drawing_commands    += 'port_label(\'output\', ' + str(port_number + 1) + ', \'' + output_name + '\')\n'

            define_output_port_datatypes += 'ssSetOutputPortDataType(S, ' + port_number_str + ', ' + signal_simulink_type + '); // ' + output_name  + ' (' + signal_type + ')\n'
            
            port_number += 1
        
        
    
        # code template
        main_fn = """/*  File    : """ + cpp_fname + """
 *  Abstract:
 *
 *      This is code that was automatically generated from an OpenRTDynamics 2 system
 *      using the Simulink s-function target. From the Matlab command prompt type
 *
 *          mex """ + cpp_fname + """
 * 
 *      to compile the s-function.
 *
 *      WARNING: Do not edit this file manually. Your changes might be lost.
 *
 *
 *  Configured input signals:
 *
""" + indent( show_inputs(m, do_not_print=True) , ' *  ') + """
 *
 *  Configured output signals:
 *
""" + indent( show_outputs(m, do_not_print=True) , ' *  ') + """
 *
 */

#include <iostream>

""" + headers + '\n' + res['algorithm_sourcecode'] + """



#define S_FUNCTION_LEVEL 2
#define S_FUNCTION_NAME  """ + self.sfun_name + """

#include "simstruc.h"

#define IS_PARAM_DOUBLE(pVal) (mxIsNumeric(pVal) && !mxIsLogical(pVal) &&\
!mxIsEmpty(pVal) && !mxIsSparse(pVal) && !mxIsComplex(pVal) && mxIsDouble(pVal))

//
// S-function methods
//

#define MDL_CHECK_PARAMETERS
#if defined(MDL_CHECK_PARAMETERS)  && defined(MATLAB_MEX_FILE)
static void mdlCheckParameters(SimStruct *S)
{

    const mxArray *pVal0 = ssGetSFcnParam(S,0);

    if ( !IS_PARAM_DOUBLE(pVal0)) {
        ssSetErrorStatus(S, "Parameter to S-function must be a double scalar");
        return;
    } 
}
#endif


static void mdlInitializeSizes(SimStruct *S)
{
    ssSetNumSFcnParams(S, 1);  /* Number of expected parameters */
#if defined(MATLAB_MEX_FILE)
    if (ssGetNumSFcnParams(S) == ssGetSFcnParamsCount(S)) {
        mdlCheckParameters(S);
        if (ssGetErrorStatus(S) != NULL) {
            return;
        }
    } else {
        return; /* Parameter mismatch will be reported by Simulink */
    }
#endif
    ssSetSFcnParamTunable(S, 0, 0);

    // number of cont and discrete states
    ssSetNumContStates(S, 0);
    ssSetNumDiscStates(S, 0);

    // number of input ports
    if (!ssSetNumInputPorts(S, """ + str(number_of_inputs) + """  )) return;
    
    // set sizes 
""" + indent( define_input_port_sizes, '    ' ) + """
    // set datatypes 
""" + indent( define_input_port_datatypes, '    ' ) + """
    // set direct feedthough (for input signals that are needed to compute the system outputs)
""" + indent( set_direct_feedthrough, '    ' ) + """
    // number of output ports
    if (!ssSetNumOutputPorts(S, """ + str(number_of_outputs) + """)) return;

""" + indent( define_output_port_sizes, '    ' ) + """
""" + indent( define_output_port_datatypes, '    ' ) + """
    // sample times
    ssSetNumSampleTimes(S, 1);
    
    // define storage
    ssSetNumRWork(S, 0);
    ssSetNumIWork(S, 0);
    ssSetNumPWork(S, 1); // reserve element in the pointers vector
    ssSetNumModes(S, 0); // to store a C++ object
    ssSetNumNonsampledZCs(S, 0);

    // operating point
    ssSetOperatingPointCompliance(S, USE_DEFAULT_OPERATING_POINT);

    // general options
    ssSetOptions(S, 0);         
}




static void mdlInitializeSampleTimes(SimStruct *S)
{
    ssSetSampleTime(S, 0, mxGetScalar(ssGetSFcnParam(S, 0)));
    ssSetOffsetTime(S, 0, 0.0);
    ssSetModelReferenceSampleTimeDefaultInheritance(S);
}

#define MDL_START
#if defined(MDL_START) 
  static void mdlStart(SimStruct *S)
  {
      ssGetPWork(S)[0] = (void *) new """ + simulation_name + """; // store new C++ object in the

      """ + simulation_name + """ *c = (""" + simulation_name + """ *) ssGetPWork(S)[0];
      
      // ORTD I/O structures
""" + indent( io_variables_define, '      ' ) + """
      // reset system
      c->step( outputs, inputs, false, false, true ); 
  }
#endif /*  MDL_START */

static void mdlOutputs(SimStruct *S, int_T tid)
{
    """ + simulation_name + """ *c = (""" + simulation_name + """ *) ssGetPWork(S)[0];
    
    // inputs
""" + indent(get_s_inputs_for_model_outputs, '    ') + """
    
    // outputs
""" + indent(get_outputs, '    ') + """
    // ORTD I/O structures
""" + indent( io_variables_define, '    ' ) + """
    
""" + indent(fill_input_values_for_model_outputs, '    ') + """

    // compute the system outputs
    c->step( outputs, inputs, true, false, false ); 
    
""" + indent(fill_output_values, '    ') + """
    
    UNUSED_ARG(tid);
}                                                


#define MDL_UPDATE
static void mdlUpdate(SimStruct *S, int_T tid)
{
    InputRealPtrsType uPtrs  = ssGetInputPortRealSignalPtrs(S,0);
    """ + simulation_name + """ *c = (""" + simulation_name + """ *) ssGetPWork(S)[0];

""" + indent( io_variables_define, '    ' ) + """
""" + indent(get_s_inputs_for_state_update, '    ') + """

    UNUSED_ARG(tid); /* not used in single tasking mode */
    
""" + indent(fill_input_values_for_state_update, '    ') + """

    // update the states of the system
    c->step( outputs, inputs, false, true, false ); 
}


static void mdlTerminate(SimStruct *S)
{
    """ + simulation_name + """ *c = (""" + simulation_name + """ *) ssGetPWork(S)[0]; // retrieve and destroy C++
    delete c;                                  // object in the termination
}                                              // function

/*=============================*
 * Required S-function trailer *
 *=============================*/

#ifdef  MATLAB_MEX_FILE    /* Is this file being compiled as a MEX-file? */
#include "simulink.c"      /* MEX-file interface mechanism */
#else
#include "cg_sfun.h"       /* Code generation registration function */
#endif


        
        """
        
        #
        # build main.cpp
        #
        main_cpp = main_fn
        
        self.files[cpp_fname] = main_cpp
        self.files[interface_fname] = icon_drawing_commands
        
        # return
        return res