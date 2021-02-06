
from . import code_generation_helper as cgh


    
def makeSignalDescription(signals, json : bool):
    signalDescription = {}
    signalDescription['names'] = cgh.signal_list_to_name_list(signals)
    signalDescription['cpptypes'] = cgh.signalListHelper_typeNames(signals)

    signalDescription['properties'] = []
    signalDescription['port_numbers'] = []
    for s in signals:
        signalDescription['properties'].append( s.properties )
        signalDescription['port_numbers'].append( s.port )

    if not json:
        # types will not be available when exported to JSON
        signalDescription['types'] = cgh.signalListHelper_types(signals)

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

    @property
    def API_name(self):
        return self.mainSimulation.API_name

    @property
    def number_of_default_ouputs(self):
        return len( self._io_outputs['calculate_output']['names'] )



    def getAPIFunctionName(self, identifier : str ):
        """
            identifier : one of 'reset', 'calculate_output', 'state_update'
        """
        return self.API_functionNames[identifier]
    


    def export_json(self):
        self.manifest = {}
        self.manifest['api_name'] = self.mainSimulation.API_name
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
