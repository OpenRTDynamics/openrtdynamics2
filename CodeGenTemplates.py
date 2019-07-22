from ExecutionCommands import *

import subprocess
import os
import json






class PutRuntimeCppHelper:
    """
        generates code for the runtime evironment
    """

    def __init__(self, mainSimulation : ExecutionCommand ):
        ExecutionCommand.__init__(self)

        self.mainSimulation = mainSimulation


    def codeGen(self):

        # build the code for the implementation
        simulationCode = self.mainSimulation.codeGen('c++', 'code')

        # the manifest containts meta-information about the simulation and its interface
        # i.e. input and output signals names and datatypes
        manifest = {}
        

        if not isinstance(self.mainSimulation.outputCommand, PutAPIFunction):
            raise('...')


        manifest['api_name'] = self.mainSimulation.getAPI_name()

        manifest['api_functions'] = {'calculate_output' : self.mainSimulation.outputCommand.nameAPI,
                                     'state_update' : self.mainSimulation.updateCommand.nameAPI,
                                     'reset' : self.mainSimulation.resetCommand.nameAPI }


        manifest['io'] = {}
        
        manifest['io']['outputs'] = {}
        manifest['io']['inputs'] = {}

        manifest['io']['outputs']['calculate_output'] = {}
        manifest['io']['inputs']['calculate_output'] = {}
        manifest['io']['inputs']['state_update'] = {}


        #
        # make strings 
        # 

        # for the output signals
        for signals in [ self.mainSimulation.outputCommand.outputSignals ]:

            # code
            # str list of output signals. e.g. 'y1, y2, y3' 
            outputNamesCSVList = ', '.join( signalListHelper_names(signals)  )
            outputNamesVarDef = '; '.join( signalListHelper_CppVarDefStr(signals)  ) + ';'
            outputPrinfPattern = ' '.join( signalListHelper_printfPattern(signals) )

            # manifest
            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            manifest['io']['outputs']['calculate_output'] = signalDescription


        # the inputs to the output command
        for signals in [ self.mainSimulation.outputCommand.inputSignals ]:

            # code
            # str list of output signals. e.g. 'y1, y2, y3' 
            input1_NamesCSVList = ', '.join( signalListHelper_names(signals)  )
            input1_NamesVarDef = '; '.join( signalListHelper_CppVarDefStr(signals)  ) + ';'
            input1PrinfPattern = ' '.join( signalListHelper_printfPattern(signals) )

            # manifest
            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            manifest['io']['inputs']['calculate_output'] = signalDescription

        # the inputs to the update command
        for signals in [ self.mainSimulation.updateCommand.inputSignals ]:

            # str list of output signals. e.g. 'y1, y2, y3' 
            input2_NamesCSVList = ', '.join( signalListHelper_names(signals)  )
            input2_NamesVarDef = '; '.join( signalListHelper_CppVarDefStr(signals)  ) + ';'
            input2_PrinfPattern = ' '.join( signalListHelper_printfPattern(signals) )

            # manifest
            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            manifest['io']['inputs']['state_update'] = signalDescription

        # all inputs
        # merge the list of inputs for the calcoutput and stateupdate function
        allInputs = list(set(self.mainSimulation.outputCommand.inputSignals + self.mainSimulation.updateCommand.inputSignals))

        for signals in [ allInputs ]:

            # str list of output signals. e.g. 'y1, y2, y3' 
            inputAll_NamesCSVList = ', '.join( signalListHelper_names(signals)  )
            inputAll_NamesVarDef = '; '.join( signalListHelper_CppVarDefStr(signals)  ) + ';'
            inputAll_PrinfPattern = ' '.join( signalListHelper_printfPattern(signals) )
        

        calcOutputsArgsList = signalListHelper_names( self.mainSimulation.outputCommand.outputSignals )
        calcOutputsArgsList.extend(  signalListHelper_names( self.mainSimulation.outputCommand.inputSignals ) )

        calcOutputsArgs = ', '.join( calcOutputsArgsList )

        # fill in template
        self.template = Template(self.template).safe_substitute(  
                                                    mainSimulationName = self.mainSimulation.getAPI_name(),
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

        self.manifest = manifest

        return self.template, self.manifest

    def writeFiles(self, folder):

        print(folder)

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

    def __init__(self, mainSimulation : ExecutionCommand, inputSignalsMapping ):

        PutRuntimeCppHelper.__init__(self, mainSimulation)

        self.inputSignalsMapping = inputSignalsMapping

        self.initCodeTemplate()

        
    def codeGen(self, iMax : int):

        # call helper to fill in some generic elements into the template
        PutRuntimeCppHelper.codeGen(self)

        #
        # make strings 
        # 

        # constant inputs
        inputConstAssignments = []
        for signal, value in self.inputSignalsMapping.items():
            inputConstAssignments.append( signal.getName() + ' = ' + str(value) )

        inputConstAssignment = '; '.join( inputConstAssignments ) + ';'

        self.sourceCode = Template(self.template).safe_substitute( iMax=iMax,
                                                                 inputConstAssignment=inputConstAssignment    ) 

        return self.sourceCode, self.manifest

    def writeCode(self, folder):
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
        outputs = range(0, len(self.mainSimulation.outputCommand.outputSignals) )

        for o in outputs:
            data.append( [] )

        for line in p.stdout.readlines():
            # print(line.decode("utf-8") )

            sample = line.decode("utf-8").split(' ')

            for o in outputs:
                data[ o ].append( float( sample[o] ) )

        # put data into a key-array
        dataStruct = { }
        o = 0
        for s in self.mainSimulation.outputCommand.outputSignals:
            dataStruct[ s.getName() ] = data[o]

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








class WasmRuntimeCpp(PutRuntimeCppHelper):
    """
        generates code for the runtime evironment

        https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html

    """

    def __init__(self, mainSimulation : ExecutionCommand, inputSignalsMapping ):

        PutRuntimeCppHelper.__init__(self, mainSimulation)

        self.inputSignalsMapping = inputSignalsMapping

        self.initCodeTemplate()

        
    def codeGen(self, iMax : int):


        #
        # make strings 
        # 

        # constant inputs
        inputConstAssignments = []
        for signal, value in self.inputSignalsMapping.items():
            inputConstAssignments.append( signal.getName() + ' = ' + str(value) )

        inputConstAssignment = '; '.join( inputConstAssignments ) + ';'


        # build I/O structs
        ioExport = self.codeGen_writeIO(self.mainSimulation.outputCommand)
        ioExport += self.codeGen_writeIO(self.mainSimulation.updateCommand)

        ioExport += self.codeGen_writeIO(self.mainSimulation.resetCommand)

        self.template = Template(self.template).safe_substitute( iMax=iMax,
                                                                    ioExport=ioExport,
                                                                 inputConstAssignment=inputConstAssignment    ) 

        # call helper to fill in some generic elements into the template
        PutRuntimeCppHelper.codeGen(self)

        self.sourceCode = self.template
        return self.template, self.manifest



    def codeGen_writeIO__(self, command_API, inputOutput : int):

        if inputOutput == 1:
            structPrefix = 'Inputs_'
            signals = command_API.inputSignals

        elif inputOutput == 2:
            structPrefix = 'Outputs_'
            signals = command_API.outputSignals

        mainSimulationName = self.mainSimulation.getAPI_name()

        lines = ''

        # Inputs
        structname = structPrefix + command_API.nameAPI 

        lines += 'value_object<' + mainSimulationName + '::' + structname + '>("' + mainSimulationName + '__' + structname + '")\n'

        for s in signals:
            fieldName = s.getName()

            lines += '.field("' + fieldName + '", &' + mainSimulationName + '::' + structname + '::' + fieldName + ')\n'

        lines += ';\n\n'


        return lines

    def codeGen_writeIO(self, command_API):
        return self.codeGen_writeIO__(command_API, 1) + self.codeGen_writeIO__(command_API, 2)


    def writeCode(self, folder):
        PutRuntimeCppHelper.writeFiles(self, folder)

        self.codeFolder = folder

        f = open(os.path.join( folder + "main.cpp"), "w")
        f.write( self.sourceCode )
        f.close()


    def build(self):

        buildCommand = "emcc --bind " + os.path.join(self.codeFolder + "main.cpp") + " -s -o " + os.path.join( self.codeFolder + "main.js" )
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


