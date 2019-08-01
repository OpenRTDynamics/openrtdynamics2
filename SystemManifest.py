
from CodeGenHelper import *


# class SystemManifest(object):

#     def __init__(self, api_name, api_functions  ):
#         self.api_name = api_name
#         self.api_functions = api_functions

#         self.inputs = {}
#         self.outputs = {}



#         manifest['io'] = {}
        
#         manifest['io']['outputs'] = {}
#         manifest['io']['inputs'] = {}

#         manifest['io']['outputs']['calculate_output'] = {}
#         manifest['io']['inputs']['calculate_output'] = {}
#         manifest['io']['inputs']['state_update'] = {}

#     def exportJSON(self):

#         manifest = {}
#         manifest['api_functions'] = self.api_functions

#         manifest['api_name'] = self.api_name

    
def makeSignalDescription(signals, json : bool):
    signalDescription = {}
    signalDescription['names'] = signalListHelper_names(signals)
    signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

    if not json:
        # types will not be available when exported to JSON
        signalDescription['types'] = signalListHelper_types(signals)

    return signalDescription


class SystemManifest(object):

    def __init__(self, mainSimulation ):

        self.mainSimulation = mainSimulation

        # the manifest containts meta-information about the simulation and its interface
        # i.e. input and output signals names and datatypes
        
        self.API_functionNames = self.mainSimulation.API_functionNames
        self.API_functions = self.mainSimulation.API_functions


        # I/O
        self._io_inputs = {}
        self._io_outputs = {}

        #
        # make strings
        # 


        for functionExportName, API_command in self.API_functions.items():
             self._io_inputs[functionExportName] = makeSignalDescription( API_command.inputSignals, json=False )
             self._io_outputs[functionExportName] = makeSignalDescription( API_command.outputSignals, json=False )


    @property
    def io_inputs(self):
        return self._io_inputs

    @property
    def io_outputs(self):
        return self._io_outputs
    


    def export_json(self):
        self.manifest = {}
        self.manifest['api_name'] = self.mainSimulation.getAPI_name()
        self.manifest['api_functions'] = self.API_functionNames

        # I/O
        io_inputs = {}
        io_outputs = {}

        for functionExportName, API_command in self.API_functions.items():
             io_inputs[functionExportName] = makeSignalDescription( API_command.inputSignals, json=True )
             io_outputs[functionExportName] = makeSignalDescription( API_command.outputSignals, json=True )


        self.manifest['io'] = {}
        self.manifest['io']['outputs'] = io_outputs
        self.manifest['io']['inputs'] = io_inputs

        return self.manifest
