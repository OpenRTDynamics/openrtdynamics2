from .code_build_commands import *
from .system_manifest import *
from .diagram_compiler import * 

import subprocess
import os
import json

# rename to SystemLibraryEntry
class SystemLibraryEntry(object):
    """
        creates a library entry
    """

    def __init__(self, compileResults : CompileResults ):

        self.compileResults = compileResults
        self.mainSimulation = compileResults.command_to_execute

        self.generate_code()

    def generate_code(self):

        # build the code for the implementation
        self._simulationCode = self.mainSimulation.generate_code('c++', 'code')

        # the manifest containts meta-information about the simulation and its interface
        # i.e. input and output signals names and datatypes
        
        self._manifest = self.compileResults.manifest #.export_json()
        
        #
        # API_functions = self.mainSimulation.API_functions

        #

        return self._simulationCode, self.manifest

    @property
    def sourceCode(self):
        return self._simulationCode

    @property
    def manifest(self):
        return self._manifest

    def writeFiles(self, folder):

        # write the system into a c++ header file

        with open( os.path.join( folder + '/' + self.manifest['api_name'] + '_manifest.json' ), 'w') as outfile:  
            json.dump(self.manifest, outfile)

    def build(self):
        pass

    def run(self):
        pass
