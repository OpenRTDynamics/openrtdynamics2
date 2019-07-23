
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

        api_functions = self.mainSimulation.API_functionNames

        # api_functions = {'calculate_output' : self.mainSimulation.outputCommand.nameAPI,
        #                              'state_update' : self.mainSimulation.updateCommand.nameAPI,
        #                              'reset' : self.mainSimulation.resetCommand.nameAPI }

        self.manifest['api_functions'] = api_functions # remove


        # I/O
        self.manifest['io'] = {}
        
        self.manifest['io']['outputs'] = {}
        self.manifest['io']['inputs'] = {}

        self.manifest['io']['outputs']['calculate_output'] = {}
        self.manifest['io']['inputs']['calculate_output'] = {}
        self.manifest['io']['inputs']['state_update'] = {}


        #
        # make strings 
        # 

        # for the output signals
        for signals in [ self.mainSimulation.outputCommand.outputSignals ]:

            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            self.manifest['io']['outputs']['calculate_output'] = signalDescription


        # the inputs to the output command
        for signals in [ self.mainSimulation.outputCommand.inputSignals ]:

            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            self.manifest['io']['inputs']['calculate_output'] = signalDescription

        # the inputs to the update command
        for signals in [ self.mainSimulation.updateCommand.inputSignals ]:

            signalDescription = {}
            signalDescription['names'] = signalListHelper_names(signals)
            signalDescription['cpptypes'] = signalListHelper_typeNames(signals)

            self.manifest['io']['inputs']['state_update'] = signalDescription

    def export_json(self):
        return self.manifest
