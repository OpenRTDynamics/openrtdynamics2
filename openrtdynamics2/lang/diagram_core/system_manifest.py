
from . import code_generation_helper as cgh


    
def make_signal_description(signals, json : bool):
    signalDescription = {}
    signalDescription['names'] = cgh.signal_list_to_name_list(signals)
    signalDescription['cpptypes'] = cgh.signalListHelper_typeNames(signals)

    signalDescription['properties'] = []
    signalDescription['port_numbers'] = []
    signalDescription['printf_patterns'] = []

    for s in signals:
        signalDescription['properties'].append( s.properties )
        signalDescription['port_numbers'].append( s.port )
        signalDescription['printf_patterns'].append( s.datatype.cpp_printf_pattern )


    if not json:
        # types will not be available when exported to JSON
        signalDescription['types'] = cgh.signalListHelper_types(signals)

    return signalDescription


class SystemManifest(object):

    def __init__(self, mainSimulation, system_inputs = None ):

        self.mainSimulation = mainSimulation

        # the manifest containts meta-information about the simulation and its interface
        # i.e. input and output signals names and datatypes
        
        self.API_functionNames = self.mainSimulation.API_functionNames
        self.API_functions = self.mainSimulation.API_functions


        # I/O
        self._io_inputs = {}
        self._io_outputs = {}
        self.system_inputs = system_inputs

        #
        # make strings
        # 

        for functionExportName, API_command in self.API_functions.items():
             self._io_inputs[functionExportName] = make_signal_description( API_command.inputSignals, json=False )
             self._io_outputs[functionExportName] = make_signal_description( API_command.outputSignals, json=False )



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
    

    # rename to to_structure
    def export_json(self):
        self.manifest = {}
        self.manifest['api_name'] = self.mainSimulation.API_name
        self.manifest['api_functions'] = self.API_functionNames

        # I/O
        io_inputs = {}
        io_outputs = {}

        for functionExportName, API_command in self.API_functions.items():
             io_inputs[functionExportName] = make_signal_description( API_command.inputSignals, json=True )
             io_outputs[functionExportName] = make_signal_description( API_command.outputSignals, json=True )


        self.manifest['io'] = {}
        self.manifest['io']['outputs'] = io_outputs
        self.manifest['io']['inputs'] = io_inputs

        # create a list of all inputs in an array whose index is the port index
        if self.system_inputs is not None:

            self.manifest['io']['all_inputs_by_port_number'] = [ None for tmo in self.system_inputs ]

            for s in self.system_inputs:

                signal_description = {}
                
                signal_description['name']            = s.name
                signal_description['properties']      = s.properties
                signal_description['cpptype']        = s.datatype.cpp_datatype_string
                signal_description['printf_patterns'] = s.datatype.cpp_printf_pattern

                self.manifest['io']['all_inputs_by_port_number'][s.port] = signal_description



        return self.manifest

