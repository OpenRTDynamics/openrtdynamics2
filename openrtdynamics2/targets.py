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


