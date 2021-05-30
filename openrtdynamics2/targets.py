from .lang.diagram_core.code_build_commands import *
from .lang.diagram_core.system_manifest import *
from .lang.diagram_core import diagram_compiler
from .lang.libraries import *

import subprocess
import os
import json
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
            
        for fname, content in self.files.items():
            fullname = os.path.join( folder + '//' + fname )
            
            print('writing file', fullname)
            
            with open( fullname, 'w') as outfile: 
                
                outfile.write( content )
                

    def build(self):
        pass

    def run(self):
        pass

