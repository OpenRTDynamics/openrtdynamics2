
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

    


class SystemManifest(object):

    def __init__(self, mainSimulation ):

        self.mainSimulation = mainSimulation

        # the manifest containts meta-information about the simulation and its interface
        # i.e. input and output signals names and datatypes
        
        self.manifest = {}
        self.manifest['api_name'] = self.mainSimulation.getAPI_name()

        API_functionNames = self.mainSimulation.API_functionNames
        API_functions = self.mainSimulation.API_functions

        self.manifest['api_functions'] = API_functionNames # remove

        # I/O
        self.manifest['io'] = {}
        self.manifest['io']['outputs'] = {}
        self.manifest['io']['inputs'] = {}

        #
        # make strings 
        # 

        def makeSignalDescription(signals):
            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            return signalDescription

        for functionExportName, API_command in API_functions.items():

             self.manifest['io']['inputs'][functionExportName] = makeSignalDescription( API_command.inputSignals )
             self.manifest['io']['outputs'][functionExportName] = makeSignalDescription( API_command.outputSignals )


        # # for the output signals
        # self.manifest['io']['outputs']['calculate_output'] = makeSignalDescription( self.mainSimulation.outputCommand.outputSignals )

        # # the inputs to the output command
        # self.manifest['io']['inputs']['calculate_output']  = makeSignalDescription( self.mainSimulation.outputCommand.inputSignals )

        # # the inputs to the update command
        # self.manifest['io']['inputs']['state_update']      = makeSignalDescription( self.mainSimulation.updateCommand.inputSignals )


    def export_json(self):
        return self.manifest
