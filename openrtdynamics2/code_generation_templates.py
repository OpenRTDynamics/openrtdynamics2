from .code_build_commands import *
from .system_manifest import *
from . import diagram_compiler
from .libraries import *

import subprocess
import os
import json
from pathlib import Path


def generate_algorithm_code( compile_results, enable_tracing=False, included_systems={} ):
    """
        generate code for the given compile result

        compile_results  - the compilation results of the a system
        enable_tracing   - include debuging
        included_systems - unused so far
    """

    main_command = compile_results.command_to_execute

    algorithm_code = ''

    # enable tracing for all execution commands
    if enable_tracing:
        # TODO: instead of putting True create an obj with a tracing infrastruture. So far printf is used automatically
        main_command.command_to_put_main_system.set_tracing_infrastructure(True)

    # combine (concatenate) the code from the library entries
    for include in included_systems:
        algorithm_code += include.sourceCode

    # build the code for the implementation
    main_command.generate_code_init('c++')
    algorithm_code += main_command.generate_code('c++', 'code')
    main_command.generate_code_destruct('c++')

    # the manifest containts meta-information about the simulation and its interface
    # i.e. input and output signals names and datatypes
    manifest = compile_results.manifest.export_json()

    return manifest, algorithm_code




class PutRuntimeCppHelper:
    """
        generates code for the runtime environment
    """

    def __init__(self, enable_tracing=False ):
        ExecutionCommand.__init__(self)  # TODO: what is this?

        # if compile_results is not None:
        #     self.compileResults = compile_results
        #     self.main_command = compile_results.command_to_execute

        # else:

        # those are set via set_compile_results after a system is compiled
        self.compileResults = None
        self.main_command = None

        #
        self._algorithm_code = None

        # list of inlcuded system
        self._includedSystems = []

        self._enable_tracing = enable_tracing

    def set_compile_results(self, compile_results : CompileResults ):
        self.compileResults = compile_results
        self.main_command = compile_results.command_to_execute

    def include_systems(self, system : SystemLibraryEntry):
        self._includedSystems = system

    def get_algorithm_code(self):
        """
            Return only the code that implement the system and all sub systems
        """
        return self._algorithm_code



    def code_gen(self):

        # generate code for the algorithm
        self.manifest, self._algorithm_code = generate_algorithm_code(self.compileResults, self._enable_tracing, self._includedSystems)

        
        # TODO: iterate over all functions present in the API of the system
        # NOTE: Currently only the main functions are used: output, update, and reset
        #
        API_functions = self.main_command.command_to_put_main_system.API_functions

        #
        # make strings 
        # 

        def makeStrings(signals):
            names_CSV_list = cgh.signal_list_to_names_string(signals)
            names_var_def = cgh.define_variable_list_string(signals)
            printf_pattern = cgh.signalListHelper_printfPattern_string(signals)

            return names_CSV_list, names_var_def, printf_pattern


        # for the output signals
        # input1_NamesCSVList; list of output signals. e.g. 'y1, y2, y3' 
        outputNamesCSVList, outputNamesVarDef, outputPrinfPattern = makeStrings( self.main_command.command_to_put_main_system.outputCommand.outputSignals )

        # the inputs to the output command
        # input1_NamesCSVList: list of output signals. e.g. 'y1, y2, y3' 
        input1_NamesCSVList, input1_NamesVarDef, input1PrinfPattern = makeStrings( self.main_command.command_to_put_main_system.outputCommand.inputSignals )

        # the inputs to the update command
        # input2_NamesCSVList list of output signals. e.g. 'u1, u2, u3' 
        input2_NamesCSVList, input2_NamesVarDef, input2_PrinfPattern = makeStrings( self.main_command.command_to_put_main_system.updateCommand.inputSignals )

        # all inputs
        # merge the list of inputs for the calcoutput and stateupdate function
        allInputs = list(set(self.main_command.command_to_put_main_system.outputCommand.inputSignals + self.main_command.command_to_put_main_system.updateCommand.inputSignals))
        inputAll_NamesCSVList, inputAll_NamesVarDef, inputAll_PrinfPattern = makeStrings( allInputs )

        # the names of input and output signals of the outputCommand combined
        calcOutputsArgs = cgh.signal_list_to_name_list( self.main_command.command_to_put_main_system.outputCommand.outputSignals + self.main_command.command_to_put_main_system.outputCommand.inputSignals )

        # fill in template
        self.template = Template(self.template).safe_substitute(  
                                                    mainSimulationName = self.main_command.command_to_put_main_system.API_name,
                                                    algorithmCode=self._algorithm_code,

                                                    input1_NamesVarDef=input1_NamesVarDef,
                                                    input1_NamesCSVList=input1_NamesCSVList,

                                                    input2_NamesVarDef=input2_NamesVarDef,
                                                    input2_NamesCSVList=input2_NamesCSVList,

                                                    inputAll_NamesVarDef=inputAll_NamesVarDef,
                                                    inputAll_NamesCSVList=inputAll_NamesCSVList,

                                                    outputNamesCSVList=outputNamesCSVList, 
                                                    outputNamesVarDef=outputNamesVarDef,
                                                    outputPrinfPattern=outputPrinfPattern,
                                                    
                                                    calcOutputsArgs=calcOutputsArgs )


        return {'sourcecode' : self.template, 'manifest' : self.manifest, 'algorithm_sourcecode' : self._algorithm_code }

    def writeFiles(self, folder):

        with open( os.path.join( folder + '//simulation_manifest.json' ), 'w') as outfile:  
            json.dump(self.manifest, outfile)

    def build(self):
        pass

    def run(self):
        pass




class PutBasicRuntimeCpp(PutRuntimeCppHelper):
    """
        generates code for the runtime evironment
    """

    def __init__(self, i_max : int, input_signals_mapping = {} ):

        self._i_max = i_max

        PutRuntimeCppHelper.__init__(self)

        self.input_signals_mapping = input_signals_mapping
        self.initCodeTemplate()

        
    def code_gen(self):

        # call helper to fill in some generic elements into the template
        code_gen_results = PutRuntimeCppHelper.code_gen(self)

        #
        # make strings 
        # 

        # constant inputs
        inputConstAssignments = []
        for signal, value in self.input_signals_mapping.items():
            inputConstAssignments.append( signal.name + ' = ' + str(value) )

        inputConstAssignment = '; '.join( inputConstAssignments ) + ';'

        self.sourceCode = Template(self.template).safe_substitute( iMax=self._i_max,
                                                                 inputConstAssignment=inputConstAssignment    ) 

        code_gen_results['sourcecode'] = self.sourceCode
        return code_gen_results

    def write_code(self, folder):
        PutRuntimeCppHelper.writeFiles(self, folder)

        self.codeFolder = folder

        f = open(os.path.join( folder + "main.cpp"), "w")
        f.write( self.sourceCode )
        f.close()


    def build(self):
        os.system("c++ " + self.codeFolder + "main.cpp -o " + self.codeFolder + "main")


    def run(self):
        # run the generated executable
        p = subprocess.Popen(self.codeFolder + 'main', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = p.wait()

        # parse csv data
        data = [ ]
        outputs = range(0, len(self.main_command.command_to_put_main_system.outputCommand.outputSignals) )

        for o in outputs:
            data.append( [] )

        for line in p.stdout.readlines():
            sample = line.decode("utf-8").split(' ')

            for o in outputs:
                data[ o ].append( float( sample[o] ) )

        # put data into a key-array
        dataStruct = { }
        o = 0
        for s in self.main_command.command_to_put_main_system.outputCommand.outputSignals:
            dataStruct[ s.name ] = data[o]

            o = o + 1

        return dataStruct


    def initCodeTemplate(self):

        #
        # template for main function in c++
        #

        self.template = """
            
#include <math.h>
#include <stdio.h>

//
// implementation of $mainSimulationName
//

$algorithmCode

//
// main
//

int main () {

    // create an instance of the simulation
    $mainSimulationName simulation;

    // input signals
    $inputAll_NamesVarDef

    // output signals
    $outputNamesVarDef

    // const assignments of the input signals
    $inputConstAssignment

    // reset the simulation
    simulation.resetStates();

    // simulate
    int i;

    for (i=0; i< $iMax; ++i) {
        simulation.calcResults_1( $calcOutputsArgs );
        simulation.updateStates(  $input2_NamesCSVList );

        printf("$outputPrinfPattern\\n", $outputNamesCSVList);
    }

}

            
        """        








class WasmRuntime(PutRuntimeCppHelper):
    """
        generates code for the Webassemble runtime environment

        https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html

    """

    def __init__(self, enable_tracing = False ):

        PutRuntimeCppHelper.__init__(self, enable_tracing=enable_tracing)

        self.initCodeTemplate()

        
    def code_gen(self):

        # build I/O structs
        ioExport = self.generate_code_writeIO(self.main_command.command_to_put_main_system.outputCommand)
        ioExport += self.generate_code_writeIO(self.main_command.command_to_put_main_system.updateCommand)

        ioExport += self.generate_code_writeIO(self.main_command.command_to_put_main_system.resetCommand)

        self.template = Template(self.template).safe_substitute( ioExport=ioExport,
                                                                 inputConstAssignment=''    ) 

        # call helper to fill in some generic elements into the template
        code_gen_results = PutRuntimeCppHelper.code_gen(self)

        self.sourceCode = self.template

        code_gen_results['sourcecode'] = self.sourceCode
        return code_gen_results



    def generate_code_writeIO__(self, command_API, inputOutput : int):

        if inputOutput == 1:
            structPrefix = 'Inputs_'
            signals = command_API.inputSignals

        elif inputOutput == 2:
            structPrefix = 'Outputs_'
            signals = command_API.outputSignals

        mainSimulationName = self.main_command.command_to_put_main_system.API_name

        lines = ''

        # Inputs
        structname = structPrefix + command_API.API_name 

        lines += 'value_object<' + mainSimulationName + '::' + structname + '>("' + mainSimulationName + '__' + structname + '")\n'

        for s in signals:
            fieldName = s.name

            lines += '.field("' + fieldName + '", &' + mainSimulationName + '::' + structname + '::' + fieldName + ')\n'

        lines += ';\n\n'


        return lines

    def generate_code_writeIO(self, command_API):
        return self.generate_code_writeIO__(command_API, 1) + self.generate_code_writeIO__(command_API, 2)


    def write_code(self, folder):

        PutRuntimeCppHelper.writeFiles(self, folder)

        self.codeFolder = folder

        f = open( Path( folder ) / "main.cpp", "w")
        f.write( self.sourceCode )
        f.close()


    def build(self):

        buildCommand = 'emcc --bind -s MODULARIZE=1 -s EXPORT_NAME="ORTD_simulator" '  + os.path.join(self.codeFolder , "main.cpp") + " -g4 -s -o " + os.path.join( self.codeFolder , "main.js" )
        print("Running compiler: " + buildCommand)

        returnCode = os.system(buildCommand)

        print( "Compilation result: ", returnCode )


    def initCodeTemplate(self):

        #
        # template for main function in c++
        #

        self.template = """
            
#include <math.h>
#include <stdio.h>
#include <emscripten/bind.h>

using namespace emscripten;

//
// implementation of $mainSimulationName
//

$algorithmCode

// Binding code
EMSCRIPTEN_BINDINGS(my_class_example) {
  class_<$mainSimulationName>("$mainSimulationName")
    .constructor<>()
    .function("resetStates", &$mainSimulationName::resetStates__)
    .function("calcResults_1", &$mainSimulationName::calcResults_1__)
    .function("updateStates", &$mainSimulationName::updateStates__)
    ;


// --------------------------------

$ioExport


}
            
        """        


