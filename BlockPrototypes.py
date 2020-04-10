from libdyn import *
from Signal import *
from Block import *
from SimulationContext import *
from BlockInterface import *
from SignalInterface import *

import CodeGenHelper as cgh

from textwrap import *

#
# block templates for common use-cases
#

class StaticSource_To1(BlockPrototype):
    """
        This defines a static source
    """
    def __init__(self, sim : Simulation, datatype ):

        self.outputType = datatype

        BlockPrototype.__init__(self, sim, [], 1)

        # output datatype is fixed
        self.outputSignal(0).setDatatype(datatype)

    def configDefineOutputTypes(self, inputTypes):

        # define the output type 
        return [ self.outputType ]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on nothing
        return []

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states

    @property
    def outputSignals(self):
        # return the output signals
        output = self.outputSignal(0)

        return output



class DynamicSource_To1(StaticSource_To1):
    """
        This defines a dynamic source
    """
    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return [] # indicates state dependency but these states do not depend on external signals



class StaticFn_1To1(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal ):

        self.u = u
        self.outputType = None

        BlockPrototype.__init__(self, sim, [ u ], 1)

    def configDefineOutputTypes(self, inputTypes):

        # just inherit the input type 
        if inputTypes[0] is not None:
            self.outputType = inputTypes[0]
        else:
            self.outputType = None

        return [ self.outputType ]        

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on the only one input signals
        return [ self.u ]

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states

    @property
    def outputSignals(self):
        # return the output signals

        return self.outputSignal(0)

    def codeGen_localvar(self, language, signal):
        # TODO: every block prototype shall befine its variables like this.. move this to BlockPrototype and remove all individual implementations

        if language == 'c++':
            return cgh.defineVariableLine( signal )





class StaticFn_NTo1(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : List[Signal] ):

        self.inputSignals = inputSignals

        BlockPrototype.__init__(self, sim, inputSignals, 1)

    def configDefineOutputTypes(self, inputTypes):

        # check if the output signal type is already defined (e.g. by the user)
        if self.outputSignal(0).getDatatype() is None:
            #
            # no output type defined so far..
            # look for an already defined input type and inherit that type.
            #

            self.outputType = computeResultingNumericType(inputTypes)

            # print('StaticFn_NTo1 (' + self.block.toStr() + '): proposed outputtype of ' + self.outputSignal(0).getName() + ' is: ' + self.outputType.toStr() + '')

        else:

            # check of the given output type is a numeric datatype
            if not isinstance( self.outputSignal(0).getDatatype(), DataTypeNumeric ):
                raise BaseException("Padd: only DataTypeNumeric can be the result/output of an addition")
        
        # return a proposal for an output type. 
        return [self.outputType]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output (there is only one) depends on all inputs
        return self.inputSignals 

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return None  # no states

    @property
    def outputSignals(self):
        # return the output signals
        output = self.outputSignal(0)

        return output

    def codeGen_localvar(self, language, signal):
        # TODO: every block prototype shall befine its variables like this.. move this to BlockPrototype and remove all individual implementations

        if language == 'c++':
            # return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'
            # return signal.datatype.cppDataType + ' ' + signal.name + ';\n'
            return cgh.defineVariableLine( signal )



class Dynamic_1To1(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal ):

        self.u = u
        self.outputType = None

        BlockPrototype.__init__(self, sim, [ u ], 1)

    def configDefineOutputTypes(self, inputTypes):

        # just inherit the input type 
        if inputTypes[0] is not None:
            self.outputType = inputTypes[0]
        else:
            self.outputType = None

        return [ self.outputType ]        

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # no (direct feedtrough) dependence on any input - only state dependent
        return [  ]

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return [self.u]  # all inputs

    @property
    def outputSignals(self):
        # return the output signals

        return self.outputSignal(0)

    def codeGen_localvar(self, language, signal):
        # TODO: every block prototype shall befine its variables like this.. move this to BlockPrototype and remove all individual implementations

        if language == 'c++':
            # return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'
            # return signal.datatype.cppDataType + ' ' + signal.name + ';\n'
            return cgh.defineVariableLine( signal )




#
# Subsystem prototypes
#

class GenericSubsystem(BlockPrototype):
    """
        Include a sub-system by passing a manifest

        - sim - the simulation this block is embedded into
        - additionalInputs - the inputs used to control the embedding block (e.g. flags that trigger if/else) (i.e. not forwarded to the embedded system)

        parameters required only in case the subsystem is already defined (e.g. loaded from a library):

        - manifest     - the manifest of the subsystem to include (optional, might be handed over by init())
        - inputSignals - the inputs to the subsystem 
        - N_outputs    - prepare a number of nOutputs (optional in case a manifest is given)
        - embedded_subsystem - the system to embed (optional)

        Note: the number of outputs must be defined either by N_outputs or by a manifest

    """
    def __init__(self, sim : Simulation = None, manifest=None, inputSignals=None, N_outputs = None, embedded_subsystem=None ):

        self.manifest = manifest
        self.inputSignals = inputSignals
        self.sim = sim
        self.Noutputs = N_outputs
        self._embedded_subsystem = embedded_subsystem

        if manifest is not None:
            if N_outputs is None:
                self.Noutputs = self.manifest.number_of_default_ouputs
            else:
                raise BaseException("N_outputs and a manifest specified at the same time")

        # output signals that were created by sth. ourside of this prototype
        # and that need to be connected to the actual outputs when init() is called.
        self.anonymous_output_signals = None

        # optional (in case this block is in charge of putting the code for the subsystem)
        self.compileResult = None

        # init super class
        BlockPrototype.__init__(self, self.sim, N_outputs = self.Noutputs)

        # Note: the inputSignals are not defined when subsystems are pre-defined in the code
        # but are automatically placed and connected by the compiler during compilation

        # check if it is already possible to init this prototype
        # (in case all requred information is available)
        if inputSignals is not None and manifest is not None:
            self.init()

        # configure datatype inheritance for the outputs signals
        for i in range(0, len( embedded_subsystem.primary_outputs )):

            output_signal_of_embedding_block = self.outputs[i]
            output_signal_of_subsystem = embedded_subsystem.primary_outputs[i]

            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )



    @property
    def embedded_subsystem(self):
        """
            Return the system that is embedded (in case it was provided, returns None otherwise)
        """

        return self._embedded_subsystem

    def set_anonymous_output_signal_to_connect(self, anonymous_output_signals):
        """
            store a list of anonymous signals to connect to the outputs of the subsystems
            after running the post_compile_callback
        """
        # List of raw signals 
        self.anonymous_output_signals = anonymous_output_signals

    def compile_callback_all_subsystems_compiled(self):
        # TODO: call init() here

        embedded_system = self._embedded_subsystem
        #
        # potential code:
        #
        self.init(embedded_system.compilationResult.manifest, embedded_system.compilationResult, embedded_system.compilationResult.inputSignals)

        
        pass
        

    # post_compile_callback (called after the subsystem to embedd was compiled)
    def init(self, manifest, compileResult, inputSignals):
        """
            This is a second phase initialization of this subsystem block

            This function shall be called when the subsystem to embedd is compiled
            after the instance of 'GenericSubsystem' is created. This way, it is possible
            to add blocks embeddeding sub-systems without haveing these subsystems to be
            already compiled.

            Optionally, the system this block belongs to can be set.

            manifest       - the system manifest of the subsystem to embedd
            compileResults - the compile results of the subsystem to embedd
            inputSignals   - input signals to the subsystem to embedd (links comming from an upper-level subsystem)

        """        

        #
        #    set the manifest of the subsystem
        #
        if self.manifest is not None:
            raise BaseException("cannot call this function as the subsystem's manifest was already defined in the constructor.")

        self.manifest = manifest

        #
        #    Set the compilation result of the embedded system (if available)
        #
        self.compileResult = compileResult

        #
        #    connect the inputs (coming from the upper-level system)
        #

        if self.inputSignals is not None:
            raise BaseException("The subsystem's inputSignals were already specified in the constructor.")

        self.inputSignals = inputSignals



        def collectDependingSignals(signals, manifestFunctionInputs):
            # collect all depending input signals (that are needed to calculate the output) in a list
            # MOVE TO A FUNCTION. MAYBE MOVE TO MANIFEST.PY
            dependingInputs = []
            for i in range( len(manifestFunctionInputs['names']) ):

                dependingInput_name = manifestFunctionInputs['names'][i]
                dependingInput_type = manifestFunctionInputs['types'][i]
                dependingInput_cpptype = manifestFunctionInputs['cpptypes'][i]

                # TODO: CHECK FOR FAILING LOOKUP
                signal = signals[ dependingInput_name ]

                # check datatype (NOTE: MOVE.. not possible here in the constructor)
                if not signal.getDatatype().cppDataType == dependingInput_cpptype:
                    raise BaseException('datatype does not match the one specified in the manifest. (' + (dependingInput_cpptype) + ' is required in the manifest)' )

                # append signal
                dependingInputs.append( signal ) 

            return dependingInputs



        # verify the number of outputs of the embedded system
        number_of_outputs_as_described_by_manifest = self.manifest.number_of_default_ouputs

        if not number_of_outputs_as_described_by_manifest == self.Noutputs:
            BaseException("missmatch in the number of outputs")

        # get the output datatypes of the embedded system
        self.outputTypes = self.manifest.io_outputs['calculate_output']['types']  


        if self.compileResult is None:
            # collect all depending input signals (that are needed to calculate the output) in a list
            self.inputsToCalculateOutputs = collectDependingSignals( self.inputSignals, self.manifest.io_inputs['calculate_output'] )

            # collect all inputs required to perform the state update
            self.inputsToUpdateStates = collectDependingSignals( self.inputSignals, self.manifest.io_inputs['state_update'] )

        else:
            # use the available compile results to get the I/O signals
            # in this case, self.inputSignals shall be a list of signals. The order
            # shall match the signal order in self.compileResults.inputSignals

            self.inputsToCalculateOutputs = self.compileResult.simulationInputSignalsToCalculateOutputs
            self.inputsToUpdateStates = self.compileResult.simulationInputSignalsToUpdateStates

            

        # combine all inputs to a list
        self.allInputs = list()

        self.allInputs.extend( self.inputsToCalculateOutputs )
        self.allInputs.extend( self.inputsToUpdateStates )

        #
        # now initialize the propotype
        #

        # define the inputs
        self.update_input_config( self.allInputs )

        # connect the outputs signals
        if self.anonymous_output_signals is not None:

            print(" -- Nesting block: connecting anonymous signals -- ")

            Ns = len(self.outputSignals)

            if not Ns == len(  self.anonymous_output_signals ):
                raise BaseException(" missmatch in the number of output signals")

            for i in range(0,Ns):
                
                s_ananon = self.anonymous_output_signals[i]
                s_source = self.outputSignals[i]

                print("connecting the output " + s_ananon.toStr() + " of the embedding block")
                s_ananon.setequal( s_source )



        # for code generation
        self.instanceVarname = self.getUniqueVarnamePrefix() + '_subsystem_' + self.manifest.API_name


    def configDefineOutputTypes(self, inputTypes):

        # the datatypes are fixed in the manifest 
        return self.outputTypes        

    def returnDependingInputs(self, outputSignal):

        # NOTE: This is a simplified veriant so far.. no dependence on the given 'outputSignal'
        #       (Every output depends on every signal in self.inputsToCalculateOutputs)

        # TODO: 6.10.19 implement this in a more granular way.
        # also use self.compileResults to get those information

        return self.inputsToCalculateOutputs

    def returnInutsToUpdateStates(self, outputSignal):
 
        # return a list of input signals that are required to update the states
        return self.inputsToUpdateStates



    def codegen_addToNamespace(self, language):
        lines = ''

        if self.compileResult is not None:
            # add the code of the subsystem
            lines = self.compileResult.commandToExecute.codeGen(language, 'code')

            if lines is None:
                raise BaseException("lines is None")

        return lines

    def codeGen_defStates(self, language):
        if language == 'c++':
            lines = '// instance of ' + self.manifest.API_name + '\n'
            lines += self.manifest.API_name + ' ' + self.instanceVarname + ';\n'

            return lines

    def codeGen_reset(self, language):
        if language == 'c++':
            return self.instanceVarname + '.' + self.manifest.getAPIFunctionName('reset') +  '();\n'

    def codeGen_localvar(self, language, signal):
        if language == 'c++':
            self.isSignalVariableDefined[ signal ] = True

            return cgh.defineVariableLine( signal )

    def codeGen_init(self, language):

        # isSignalVariableDefined contains for each output signal a flag that indicates wheter veriables 
        # for these output signals shall be defined (i.e., memory reserved)
        self.isSignalVariableDefined = {}
        for s in self.outputSignals:
            self.isSignalVariableDefined[ s ] = False

    def codeGen_destruct(self, language):
        pass

    def codeGen_call_OutputFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('calculate_output') +  '(' + cgh.signalListHelper_names_string(self.outputSignals + self.inputsToCalculateOutputs) + ');\n'

    def codeGen_call_UpdateFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('state_update') +  '(' + cgh.signalListHelper_names_string(self.inputsToUpdateStates) + ');\n'

    def codeGen_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = ''
            
            for signal, isDefined in self.isSignalVariableDefined.items():
                # if the signal is not a simulation output

                if not isDefined:

                    lines += cgh.defineVariable( signal ) 

                    if signal not in signals:
                        lines += ' // NOTE: unused output signal\n'
                    else:
                        lines += '\n'

                    self.isSignalVariableDefined[ signal ] = True

            lines += self.codeGen_call_OutputFunction(self.instanceVarname, self.manifest, language)

        return lines

    def codeGen_update(self, language):
        if language == 'c++':

            # input to this call are the signals in self.inputsToUpdateStates
            return self.codeGen_call_UpdateFunction(self.instanceVarname, self.manifest, language)

def generic_subsystem( manifest, inputSignals : List[SignalUserTemplate] ):
    return wrap_signal_list( GenericSubsystem(get_simulation_context(), manifest, unwrap_hash(inputSignals) ).outputSignals )








class MultiSubsystemEmbedder(BlockPrototype):
    """
        Include a switch including multiple sub-systems 

        - additional_inputs       - inputs used to control the switching strategy
        - subsystem_prototypes    - a list of the prototypes of all subsystems (of type GenericSubsystem)
        - reference_outputs : List [Signal] - output signals of the reference subsystem from which the output datatypes are inherited

    """
    def __init__(self, sim : Simulation, additional_inputs : List [Signal], subsystem_prototypes : List [GenericSubsystem], reference_outputs : List [Signal] ):

        self._subsystem_prototypes = subsystem_prototypes
        
        # analyze the default subsystem (the first) to get the output datatypes to use
        # NOTE: not possible, reference_subsystem.outputs does not exist so far
        reference_subsystem = self._subsystem_prototypes[0]
        self._number_of_outputs_of_all_nested_systems = len(reference_subsystem.outputs)


        # assertion
        for subsystem_prototype in self._subsystem_prototypes:
            if not len(subsystem_prototype.outputs) == self._number_of_outputs_of_all_nested_systems:
                raise BaseException("all subsystems must have the same number of outputs")


        BlockPrototype.__init__(self, sim=sim, inputSignals=None, N_outputs = self._number_of_outputs_of_all_nested_systems )

        # control inputs that are used to control how the subsystems are handled
        self._additional_inputs = additional_inputs 

        # a list of the prototypes of all subsystems
        self._subsystem_prototypes = subsystem_prototypes

        # compile results of the subsystems
        self._compile_result_list = None

        # a list of all inputs used by all subsystems
        self._list_of_all_subsystem_inputs = None

        # a list of all inputs including self._list_of_all_subsystem_inputs and self._additional_inputs
        self._list_of_all_inputs = None

        # inherit output datatypes of the reference subsystem
        for i in range(0, len( self.outputs )):

            output_signal_of_embedding_block = self.outputs[i]
            output_signal_of_subsystem = reference_outputs[i]
            output_signal_of_embedding_block.inherit_datatype_from_signal( output_signal_of_subsystem )


    def compile_callback_all_subsystems_compiled(self):

        # collect a set of all inputs of each subsystem
        set_of_all_inputs = set()

        for subsystem_prototype in self._subsystem_prototypes:
            set_of_all_inputs.update( subsystem_prototype.inputs )

        self._list_of_all_subsystem_inputs = list( set_of_all_inputs )

        # add additional inputs
        set_of_all_inputs.update( self._additional_inputs )

        self._list_of_all_inputs = list(set_of_all_inputs)
            


    def compile_callback_all_datatypes_defined(self):
        pass



    def returnDependingInputs(self, outputSignal):

        # NOTE: This is a simplified veriant so far..
        #       Every output depends on every signal

        return self._list_of_all_inputs
        

    def returnInutsToUpdateStates(self, outputSignal):
 
        # NOTE: This is a simplified veriant so far..
        #       Every output depends on every signal

        return self._list_of_all_inputs



    # this overwrites the method of the super class
    def codegen_addToNamespace(self, language):

        lines = ''

        # generate the code for each subsystem
        print("SwitchSubsystem: building code for each subsystem.")

        if self._compile_result_list is not None:
            # add the code of the subsystem

            for cr in self._compile_result_list:
                lines += cr.commandToExecute.codeGen(language, 'code')


        return lines



    def codeGen_localvar(self, language, signal):
        if language == 'c++':

            return GenericSubsystem.codeGen_localvar(self, language, signal)


    def generate_subsystem_embedder(self, language, system_prototype, ouput_signals : List [ Signal ]):

        lines = '{ // subsystem ' + system_prototype.embedded_subsystem.name + '\n'

        innerLines = system_prototype.codeGen_output_list(language, system_prototype.outputs)

        for i in range( 0, len( ouput_signals ) ):
            innerLines += cgh.asign( system_prototype.outputs[i], ouput_signals[i] )

        lines += indent(innerLines, '  ')
        lines += '}\n'

        return lines

    def generate_if_else(self, language, condition_list, action_list):

        N = len(condition_list)

        lines = 'if (' + condition_list[0] + ') ' + action_list[0]

        for i in range(1, N):
            lines += 'else if (' + condition_list[i] + ') ' + action_list[i]

        if len(action_list) == N + 1:
            lines += 'else ' + action_list[0]

        elif len(action_list) > N + 1:
            raise BaseException("too many actions given")

        return lines

    def generate_compare_equality_to_constant( self, language, signal : Signal, constant ):
        return signal.name + ' == ' + str(constant)

    
    def generate_switch( self, language, switch_control_signal : Signal, switch_ouput_signals : List [ Signal ] ):

        lines = ''

        action_list = []
        condition_list = []

        subsystem_counter = 0
        for system_prototype in self._subsystem_prototypes:

            # call each subsystem embedder to generate its code
            action_list.append( self.generate_subsystem_embedder( language, system_prototype, switch_ouput_signals ) )

            # generate conditions when to execute the respective subsystem 
            condition_list.append( self.generate_compare_equality_to_constant( language, switch_control_signal , subsystem_counter ) )

            subsystem_counter += 1

        # combine conditions and their repective actions
        lines += self.generate_if_else(language, condition_list, action_list)

        return lines


    def codeGen_output_list(self, language, signals : List [ Signal ] ):

        lines = ''
        if language == 'c++':
            lines += cgh.defineVariables( signals ) + '\n'

            lines += self.generate_switch( language=language, switch_control_signal=self._additional_inputs[0], switch_ouput_signals=signals )


        return lines

    def codeGen_call_UpdateFunction(self, instanceVarname, manifest, language):

        lines = ''
        # lines += GenericSubsystem.codeGen_call_UpdateFunction(self, instanceVarname, manifest, language)

        return lines
        









class TruggeredSubsystem(GenericSubsystem):
    """
        Include a triggered sub-system

        Optional:

            prevent_output_computation = True: 
                The subsystems outputs are only computed when triggered. Please note that the outputs
                of the subsystem are uninitialized until the subsystem is triggered.

    """
    def __init__(self, sim : Simulation, manifest, inputSignals, trigger : Signal, N_outputs = None, prevent_output_computation = False ):

        # TODO: add this signal to the blocks inputs
        self.triggerSignal = trigger
        self.prevent_output_computation = prevent_output_computation

        GenericSubsystem.__init__(self, 
                                    sim=sim, 
                                    manifest=manifest, 
                                    inputSignals=inputSignals, 
                                    N_outputs = N_outputs, 
                                    additionalInputs=[ trigger ] )

    def returnDependingInputs(self, outputSignal):

        # NOTE: This is a simplified veriant so far.. no dependence on the given 'outputSignal'
        #       (Every output depends on every signal in dependingInputs)

        dependingInputs = GenericSubsystem.returnDependingInputs(self, outputSignal)

        # NOTE: important here to make a copy of the list returned by GenericSubsystem.
        #       otherwise the original list would be modified by append.
        dependingInputsOuter = dependingInputs.copy()
        
        dependingInputsOuter.append( self.triggerSignal )

        return dependingInputsOuter
        


    def codeGen_localvar(self, language, signal):
        if language == 'c++':

            return GenericSubsystem.codeGen_localvar(self, language, signal)


    def codeGen_call_OutputFunction(self, instanceVarname, manifest, language):

        if self.prevent_output_computation:
            # the subsystems outputs are only computed when triggered
            lines = 'if (' +  self.triggerSignal.name + ') {\n'
            lines += GenericSubsystem.codeGen_call_OutputFunction(self, instanceVarname, manifest, language)
            lines += '}\n'
        else:
            # the subsystems outputs are always computed
            lines = GenericSubsystem.codeGen_call_OutputFunction(self, instanceVarname, manifest, language)


        return lines

    def codeGen_call_UpdateFunction(self, instanceVarname, manifest, language):
        lines = 'if (' +  self.triggerSignal.name + ') {\n'
        lines += GenericSubsystem.codeGen_call_UpdateFunction(self, instanceVarname, manifest, language)
        lines += '}\n'

        return lines
        
def triggered_subsystem( manifest, inputSignals : List[SignalUserTemplate], trigger : SignalUserTemplate, prevent_output_computation = False ):
    return wrap_signal_list( TruggeredSubsystem( get_simulation_context(), manifest, unwrap_hash( inputSignals, prevent_output_computation ), unwrap( trigger ) ).outputSignals )

        





class ForLoopSubsystem(GenericSubsystem):
    """
        Include a triggered sub-system
    """
    def __init__(self, sim : Simulation, manifest, inputSignals, i_max : Signal ):

        # TODO: add this signal to the blocks inputs
        self.i_max_signal = i_max

        GenericSubsystem.__init__(self, sim=sim, manifest=manifest, inputSignals=inputSignals, additionalInputs=[ i_max ] )

    def returnDependingInputs(self, outputSignal):

        # NOTE: This is a simplified variant so far.. no dependence on the given 'outputSignal'
        #       (Every output depends on every signal in dependingInputs)

        dependingInputs = GenericSubsystem.returnDependingInputs(self, outputSignal)

        # NOTE: important here to make a copy of the list returned by GenericSubsystem.
        #       otherwise the original list would be modified by append.
        dependingInputsOuter = dependingInputs.copy()
        
        dependingInputsOuter.append( self.i_max_signal )

        return dependingInputsOuter
        


    def codeGen_localvar(self, language, signal):
        if language == 'c++':

            return GenericSubsystem.codeGen_localvar(self, language, signal)


    def codeGen_call_OutputFunction(self, instanceVarname, manifest, language):
        lines = 'for (int i = 0; i < '  +  self.i_max_signal.name + '; ++i) {\n'
        lines += GenericSubsystem.codeGen_call_OutputFunction(self, instanceVarname, manifest, language)
        lines += GenericSubsystem.codeGen_call_UpdateFunction(self, instanceVarname, manifest, language)
        lines += '}\n'

        return lines

    def codeGen_call_UpdateFunction(self, instanceVarname, manifest, language):
        # lines = 'if (' +  self.triggerSignal.name + ') {\n'
        # lines += '}\n'

        lines = ''

        return lines
        
def for_loop_subsystem( manifest, inputSignals : List[SignalUserTemplate], i_max : SignalUserTemplate ):
    return wrap_signal_list( ForLoopSubsystem( get_simulation_context(), manifest, unwrap_hash( inputSignals ), unwrap( i_max ) ).outputSignals )

        



            


#
# Sources
#

class Const(StaticSource_To1):
    def __init__(self, sim : Simulation, constant, datatype ):

        self.constant = constant

        # call super
        StaticSource_To1.__init__(self, sim, datatype)

    # def codeGen_localvar(self, language):
    #     if language == 'c++':
    #         # return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'
    #         return signal.datatype.cppDataType + ' ' + signal.name + ';\n'


    def codeGen_localvar(self, language, signal):
        if language == 'c++':
            return cgh.defineVariableLine( signal )

    #def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str( self.constant ) + ';\n'

def dyn_const(sim : Simulation, constant, datatype ):
    return wrap_signal( Const(sim, constant, datatype).outputSignals )

def const(constant, datatype ):
    return wrap_signal( Const(get_simulation_context(), constant, datatype).outputSignals )




#
# Multiply by constant
#

class Gain(StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, factor : float ):

        self._factor = factor

        StaticFn_1To1.__init__(self, sim, u)

    def codeGen_output_list(self, language, signals : List [ Signal ] ):
    #def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            # return self.outputSignal(0).getName() + ' = ' + str(self._factor) + ' * ' + self.inputSignal(0).getName() +  ';\n'
            return signals[0].name + ' = ' + str(self._factor) + ' * ' + self.inputSignal(0).name +  ';\n'

def dyn_gain(sim : Simulation, u : Signal, gain : float ):
    return wrap_signal( Gain(sim, u.unwrap, gain).outputSignals )

def gain(u : SignalUserTemplate, gain : float ):
    return wrap_signal( Gain(get_simulation_context(), u.unwrap, gain).outputSignals )


#
# Cast to given datatype
#

class ConvertDatatype(StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, target_type : DataType ):

        self._target_type = target_type

        StaticFn_1To1.__init__(self, sim, u)

    def configDefineOutputTypes(self, inputTypes):
        return [ self._target_type ]  

    #def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            # TODO: only = is used and the c++ compiler decides how to convert...
            return signals[0].name + ' = ' + self.inputSignal(0).name + ';\n'

def convert(u : SignalUserTemplate, target_type : DataType ):
    return wrap_signal( ConvertDatatype(get_simulation_context(), u.unwrap, target_type).outputSignals )



#
# Basic operators
#

class Add(StaticFn_NTo1):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], factors : List[float] ):

        # feasibility checks
        if len(inputSignals) != len(factors):
            raise("len(inp_list) must be equal to len(factors)")

        self.factors = factors
        StaticFn_NTo1.__init__(self, sim, inputSignals)

    #def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(self.factors[i]) + ' * ' + s.getName() )
                i = i + 1

            sumline = ' + '.join( strs )
            lines = signals[0].name + ' = ' + sumline + ';\n'

            return lines

def dyn_add(sim : Simulation, inputSignals : List[SignalUserTemplate], factors : List[float]):
    return wrap_signal( Add(sim, unwrap_list( inputSignals ), factors).outputSignals )

def add(inputSignals : List[SignalUserTemplate], factors : List[float]):
    return wrap_signal( Add(get_simulation_context(), unwrap_list( inputSignals ), factors).outputSignals )


class Operator1(StaticFn_NTo1):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], operator : str ):

        self.operator = operator
        StaticFn_NTo1.__init__(self, sim, inputSignals)

    #def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(  s.getName() ) )
                i = i + 1

            sumline = (' ' + self.operator + ' ').join( strs )
            lines = signals[0].name + ' = ' + sumline + ';\n'

            return lines


def dyn_operator1(sim : Simulation, inputSignals : List[SignalUserTemplate], operator : str ):
    return wrap_signal( Operator1(sim, unwrap_list( inputSignals ), operator).outputSignals )

def operator1(inputSignals : List[SignalUserTemplate], operator : str ):
    return wrap_signal( Operator1(get_simulation_context(), unwrap_list( inputSignals ), operator).outputSignals )






class ComparisionOperator(StaticFn_NTo1):
    def __init__(self, sim : Simulation, left : Signal, right : Signal, operator : str ):

        self.operator = operator

        StaticFn_NTo1.__init__(self, sim, inputSignals = [left, right])

    def configDefineOutputTypes(self, inputTypes):

        # return a proposal for an output type. 
        return [ DataTypeBoolean(1) ]

    # def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = signals[0].name + ' = ' + self.inputSignals[0].name + ' ' + self.operator + ' ' + self.inputSignals[1].name + ';\n'
            return lines


def comparison(left : SignalUserTemplate, right : SignalUserTemplate, operator : str ):
    return wrap_signal( ComparisionOperator(get_simulation_context(), left.unwrap, right.unwrap, operator).outputSignals )







class SwitchNto1(StaticFn_NTo1):
    def __init__(self, sim : Simulation, state : Signal, inputs : List [Signal] ):

        self.inputs = inputs
        self.state = state

        inputSignals = [state]
        inputSignals.extend(inputs)

        StaticFn_NTo1.__init__(self, sim, inputSignals )

    def configDefineOutputTypes(self, inputTypes):

        # check weather the trigger input is int32
        if inputTypes[0] is not None:
            if DataTypeInt32(1).isEqualTo( inputTypes[0] ) == 0:
                raise BaseException('state input must be of type Int32')  

        # determine a guess for the output datatype
        # check if all given datatypes are equal
        autoDatatype = autoDatatype_Nto1(self.outputSignal(0).getDatatype(), inputTypes[1:-1] )

        return [ autoDatatype ] # DataTypeFloat64(1)

    #def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):

        if language == 'c++':
            lines = '\n// switch ' + str(len(self.inputs)) + ' inputs --> ' + self.state.name + '\n'
            i = 1
            for ip in self.inputs:
                if i == 1:
                    lines += 'if (' + self.state.name + ' == ' + str(i) + ') {\n'
                else:
                    lines += 'else if (' + self.state.name + ' == ' + str(i) + ') {\n'

                lines += '  ' + signals[0].name + ' = ' + ip.name + ';\n'
                lines += '} '

                i += 1

            lines += 'else {\n'
            lines += '  ' + signals[0].name + ' = ' + self.inputs[0].name + ';\n'
            lines += '}\n'
            
            return lines


def switchNto1( state : SignalUserTemplate, inputs : SignalUserTemplate ):
    return wrap_signal( SwitchNto1(get_simulation_context(), state.unwrap, unwrap_list(inputs) ).outputSignals )





#
# Static functions that map 1 --> 1
#

class StaticFnByName_1To1(StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, functionName : str ):

        self._functionName = functionName

        StaticFn_1To1.__init__(self, sim, u)

    # def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + str(self._functionName) + '(' + self.inputSignal(0).getName() +  ');\n'


def dyn_sin(sim : Simulation, u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(sim, u.unwrap, 'sin').outputSignals )

def dyn_cos(sim : Simulation, u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(sim, u.unwrap, 'cos').outputSignals )

def sin(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'sin').outputSignals )

def cos(u : SignalUserTemplate ):
    return wrap_signal( StaticFnByName_1To1(get_simulation_context(), u.unwrap, 'cos').outputSignals )



#
# Blocks that have an internal memory
#

class Delay(Dynamic_1To1):
    def __init__(self, sim : Simulation, u : Signal, initial_state = None ):

        self._initial_state = initial_state

        StaticFn_1To1.__init__(self, sim, u)

    def codeGen_defStates(self, language):
        if language == 'c++':
            return self.outputType.cppDataType + ' ' + self.getUniqueVarnamePrefix() + '_delayed' + ';\n'

    #def codeGen_output(self, language, signal : Signal):
    def codeGen_output_list(self, language, signals : List [ Signal ] ):
        if language == 'c++':
            return signals[0].name + ' = ' + self.getUniqueVarnamePrefix() + '_delayed' + ';\n'

    def codeGen_update(self, language):
        if language == 'c++':
            return self.getUniqueVarnamePrefix() + '_delayed' + ' = ' + self.inputSignal(0).getName() + ';\n'

    def codeGen_reset(self, language):
        if language == 'c++':

            if self._initial_state is None:
                # get the zero element for the given datatype
                initial_state_str = str(self.outputType.cpp_zero_element)
            else:
                initial_state_str = str(self._initial_state)

            return self.getUniqueVarnamePrefix() + '_delayed' + ' = ' + initial_state_str + ';\n'


def dyn_delay(sim : Simulation, u : SignalUserTemplate, initial_state = None ):
    return wrap_signal( Delay(sim, u.unwrap, initial_state ).outputSignals )

def delay(u : SignalUserTemplate, initial_state = None):
    return wrap_signal( Delay(get_simulation_context(), u.unwrap, initial_state ).outputSignals )



