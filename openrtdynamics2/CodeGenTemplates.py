from .ExecutionCommands import *
from .SystemManifest import *
from . import CompileDiagram
from .SystemLibrary import *

import subprocess
import os
import json
from pathlib import Path


class PutRuntimeCppHelper:
    """
        generates code for the runtime evironment
    """

    def __init__(self, compile_results : CompileResults = None, enable_tracing=False ):
        ExecutionCommand.__init__(self)  # TODO: what is this?

        if compile_results is not None:
            self.compileResults = compile_results
            self.mainSimulation = compile_results.commandToExecute

        else:
            self.compileResults = None
            self.mainSimulation = None

        # list of inlcuded system
        self._includedSystems = []

        self._enable_tracing = enable_tracing

    def set_compile_results(self, compile_results : CompileResults ):
        self.compileResults = compile_results
        self.mainSimulation = compile_results.commandToExecute

    def include_systems(self, system : SystemLibraryEntry):
        self._includedSystems = system

    def code_gen(self):

        simulationCode = ''

        # enable tracing for all execution commands
        if self._enable_tracing:
            # TODO: instead of putting True create an obj with a tracing infrastruture. So far printf is used automatically
            self.mainSimulation.command_to_put_main_system.set_tracing_infrastructure(True)

        # combine (concatenate) the code from the library entries
        for include in self._includedSystems:
            simulationCode += include.sourceCode

        # build the code for the implementation
        self.mainSimulation.generate_code_init('c++')
        simulationCode += self.mainSimulation.generate_code('c++', 'code')
        self.mainSimulation.generate_code_destruct('c++')

        # the manifest containts meta-information about the simulation and its interface
        # i.e. input and output signals names and datatypes
        
        self.manifest = self.compileResults.manifest.export_json()
        
        # TODO: iterate over all functions present in the API of the system
        # NOTE: Currently only the main functions are used: output, update, and reset
        #
        API_functions = self.mainSimulation.command_to_put_main_system.API_functions

        #
        # make strings 
        # 

        def makeStrings(signals):
            namesCSVList = cgh.signal_list_to_names_string(signals)
            namesVarDef = cgh.define_variable_list_string(signals)
            prinfPattern = cgh.signalListHelper_printfPattern_string(signals)

            return namesCSVList, namesVarDef, prinfPattern


        # for the output signals
        # input1_NamesCSVList; list of output signals. e.g. 'y1, y2, y3' 
        outputNamesCSVList, outputNamesVarDef, outputPrinfPattern = makeStrings( self.mainSimulation.command_to_put_main_system.outputCommand.outputSignals )

        # the inputs to the output command
        # input1_NamesCSVList: list of output signals. e.g. 'y1, y2, y3' 
        input1_NamesCSVList, input1_NamesVarDef, input1PrinfPattern = makeStrings( self.mainSimulation.command_to_put_main_system.outputCommand.inputSignals )

        # the inputs to the update command
        # input2_NamesCSVList list of output signals. e.g. 'u1, u2, u3' 
        input2_NamesCSVList, input2_NamesVarDef, input2_PrinfPattern = makeStrings( self.mainSimulation.command_to_put_main_system.updateCommand.inputSignals )

        # all inputs
        # merge the list of inputs for the calcoutput and stateupdate function
        allInputs = list(set(self.mainSimulation.command_to_put_main_system.outputCommand.inputSignals + self.mainSimulation.command_to_put_main_system.updateCommand.inputSignals))
        inputAll_NamesCSVList, inputAll_NamesVarDef, inputAll_PrinfPattern = makeStrings( allInputs )

        # the names of input and output signals of the outputCommand combined

        # old variant
        #
        # calcOutputsArgsList = signal_list_to_name_list( self.mainSimulation.outputCommand.outputSignals )
        # calcOutputsArgsList.extend(  signal_list_to_name_list( self.mainSimulation.outputCommand.inputSignals ) )
        # calcOutputsArgs = ', '.join( calcOutputsArgsList )

        calcOutputsArgs = cgh.signal_list_to_name_list( self.mainSimulation.command_to_put_main_system.outputCommand.outputSignals + self.mainSimulation.command_to_put_main_system.outputCommand.inputSignals )

        # fill in template
        self.template = Template(self.template).safe_substitute(  
                                                    mainSimulationName = self.mainSimulation.command_to_put_main_system.API_name,
                                                    simulationCode=simulationCode,

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


        return self.template, self.manifest

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

    def __init__(self, input_signals_mapping = {} ):

        PutRuntimeCppHelper.__init__(self)

        self.input_signals_mapping = input_signals_mapping
        self.initCodeTemplate()

        
    def code_gen(self, iMax : int):

        # call helper to fill in some generic elements into the template
        PutRuntimeCppHelper.code_gen(self)

        #
        # make strings 
        # 

        # constant inputs
        inputConstAssignments = []
        for signal, value in self.input_signals_mapping.items():
            inputConstAssignments.append( signal.name + ' = ' + str(value) )

        inputConstAssignment = '; '.join( inputConstAssignments ) + ';'

        self.sourceCode = Template(self.template).safe_substitute( iMax=iMax,
                                                                 inputConstAssignment=inputConstAssignment    ) 

        return self.sourceCode, self.manifest

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
        outputs = range(0, len(self.mainSimulation.command_to_put_main_system.outputCommand.outputSignals) )

        for o in outputs:
            data.append( [] )

        for line in p.stdout.readlines():
            sample = line.decode("utf-8").split(' ')

            for o in outputs:
                data[ o ].append( float( sample[o] ) )

        # put data into a key-array
        dataStruct = { }
        o = 0
        for s in self.mainSimulation.command_to_put_main_system.outputCommand.outputSignals:
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

$simulationCode

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
        generates code for the Webassemble runtime evironment

        https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html

    """

    def __init__(self, input_signals_mapping = {}, enable_tracing = False ):

        PutRuntimeCppHelper.__init__(self, enable_tracing=enable_tracing)

        self.input_signals_mapping = input_signals_mapping
        self.initCodeTemplate()

        
    def code_gen(self):


        #
        # make strings 
        # 

        # constant inputs
        inputConstAssignments = []
        for signal, value in self.input_signals_mapping.items():
            inputConstAssignments.append( signal.name + ' = ' + str(value) )

        inputConstAssignment = '; '.join( inputConstAssignments ) + ';'


        # build I/O structs
        ioExport = self.generate_code_writeIO(self.mainSimulation.command_to_put_main_system.outputCommand)
        ioExport += self.generate_code_writeIO(self.mainSimulation.command_to_put_main_system.updateCommand)

        ioExport += self.generate_code_writeIO(self.mainSimulation.command_to_put_main_system.resetCommand)

        self.template = Template(self.template).safe_substitute( ioExport=ioExport,
                                                                 inputConstAssignment=inputConstAssignment    ) 

        # call helper to fill in some generic elements into the template
        PutRuntimeCppHelper.code_gen(self)

        self.sourceCode = self.template
        return self.template, self.manifest



    def generate_code_writeIO__(self, command_API, inputOutput : int):

        if inputOutput == 1:
            structPrefix = 'Inputs_'
            signals = command_API.inputSignals

        elif inputOutput == 2:
            structPrefix = 'Outputs_'
            signals = command_API.outputSignals

        mainSimulationName = self.mainSimulation.command_to_put_main_system.API_name

        lines = ''

        # Inputs
        structname = structPrefix + command_API.nameAPI 

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

$simulationCode

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


