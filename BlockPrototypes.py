from libdyn import *
from Signal import *
from Block import *
from SimulationContext import *
from BlockInterface import *
from SignalInterface import *

import CodeGenHelper as cgh

#
# block templates for common use-cases
#

class StaticSource_To1(BlockPrototype):
    """
        This defines a static source
    """
    def __init__(self, sim : Simulation, datatype ):

        self.outputType = datatype

        BlockPrototype.__init__(self, sim, None, 1)

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
    """
    def __init__(self, sim : Simulation, manifest, inputSignals, additionalInputs : List[ Signal ] = None ):
        # intputSignals is a hash array
        #
        # intputSignals = {'in1': in1, 'in2', : in2}

        self.manifest = manifest
        self.inputSignals = inputSignals
        self.sim = sim
        self.additionalInputs = additionalInputs

        # optional (in case this block is in charge of putting the code for the subsystem)
        self.compileResult = None

        # if input signals are already defined
        #
        # Note: the inputSignals are not defined when subsystems are pre-defined in the code
        # but are automatically placed and connected by the compiler during compilation

        # 
        if inputSignals is not None and manifest is not None:
            self.init()

    def set_manifest(self, manifest):
        """
            set the manifest of the subsystem
        """

        if self.manifest is not None:
            raise BaseException("cannot call this function as the subsystem's manifest was already specified in the constructor.")

        self.manifest = manifest

    def set_compile_result(self, compileResult):
        """
            Set the compilation result of the embedded system (if available)
        """
        self.compileResult = compileResult

    def set_inputSignals(self, inputSignals):
        """
            connect the inputs (coming from the upper-level system)
        """

        if self.inputSignals is not None:
            raise BaseException("cannot call this function as the subsystem's inputSignals were already specified in the constructor.")

        self.inputSignals = inputSignals

        


    def init(self, sim : Simulation):
        """
            This is a second phase initialization of this subsystem block

            This function shall be called when the subsystem to embedd is compiled
            after the instance of 'GenericSubsystem' is created. This way, it is possible
            to add blocks embeddeding sub-systems without haveing these subsystems to be
            already compiled.

            Optionally, the system this block belongs to can be set.
        """        
        
        if self.manifest is None:
            raise BaseException("the subsystem's manifest was not specified.")

        if self.inputSignals is None:
            raise BaseException("the subsystem's inputSignals were not specified.")

        if sim is not None:
            self.sim = sim

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



        # the number of outputs of the embedded system
        self.Noutputs = len( self.manifest.io_outputs['calculate_output']['names'] )

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
        if self.additionalInputs is not None:
            self.allInputs = self.additionalInputs

        else:
            self.allInputs = list()

        #
        self.allInputs.extend( self.inputsToCalculateOutputs )
        self.allInputs.extend( self.inputsToUpdateStates )

        # now initialize the propotype
        if self.compileResult is None:
            BlockPrototype.__init__(self, self.sim, self.allInputs, self.Noutputs)

        else:
            output_datatypes = extract_datatypes_from_signals(self.compileResult.outputSignals)
            BlockPrototype.__init__(self, self.sim, self.allInputs, self.Noutputs, datatypes=output_datatypes)

        # for code generation
        self.instanceVarname = self.getUniqueVarnamePrefix() + '_subsystem_' + self.manifest.API_name

        
    @property
    def embeddedSystemsInputs(self):
        """
            the input signals forwarded to the embedded system
        """
        return self._XXX

    @property
    def embeddedSystemsOutputs(self):
        """
            the output signals forwarded to the embedded system
        """
        return self._XXX

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
        self.codeGen_outputsCalculated = False

        # isSignalVariableDefined contains for each output signal a flag that indicates wheter veriables 
        # for these output signals shall be defined (i.e. memory reserved)
        self.isSignalVariableDefined = {}
        for s in self.outputSignals:
            self.isSignalVariableDefined[ s ] = False

    def codeGen_destruct(self, language):
        pass

    def codeGen_setOutputReference(self, language, signal):
        # infcates that for signal, no localvar will be created, but a reference to that data is used
        # This is the case for signals that are system outputs

        # 
        self.isSignalVariableDefined[ signal ] = True


    def codeGen_call_OutputFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('calculate_output') +  '(' + cgh.signalListHelper_names_string(self.outputSignals + self.inputsToCalculateOutputs) + ');\n'

    def codeGen_call_UpdateFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('state_update') +  '(' + cgh.signalListHelper_names_string(self.inputsToUpdateStates) + ');\n'


    def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            lines = ''

            for signal, isDefined in self.isSignalVariableDefined.items():
                # if the signal is not a simulation output

                if not isDefined:   # and not signal.codeGen_memoryReserved:
                    lines += cgh.defineVariable( signal ) + ' // NOTE: unused output signal\n'
                    self.isSignalVariableDefined[ signal ] = True

            if not self.codeGen_outputsCalculated:
                # input to this call are the signals in self.inputsToCalculateOutputs

                lines += self.codeGen_call_OutputFunction(self.instanceVarname, self.manifest, language)

                self.codeGen_outputsCalculated = True

            else:
                lines = ''

        return lines

    def codeGen_update(self, language):
        if language == 'c++':

            # input to this call are the signals in self.inputsToUpdateStates
            return self.codeGen_call_UpdateFunction(self.instanceVarname, self.manifest, language)

def generic_subsystem( manifest, inputSignals : List[SignalUserTemplate] ):
    return wrap_signal_list( GenericSubsystem(get_simulation_context(), manifest, unwrap_hash(inputSignals) ).outputSignals )





class TruggeredSubsystem(GenericSubsystem):
    """
        Include a triggered sub-system by passing a manifest
    """
    def __init__(self, sim : Simulation, manifest, inputSignals, trigger : Signal ):

        # TODO: add this signal to the blocks inputs
        self.triggerSignal = trigger

        GenericSubsystem.__init__(self, sim=sim, manifest=manifest, inputSignals=inputSignals, additionalInputs=[ trigger ] )

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
        lines = 'if (' +  self.triggerSignal.name + ') {\n'
        lines += GenericSubsystem.codeGen_call_OutputFunction(self, instanceVarname, manifest, language)
        lines += '}\n'

        return lines

    def codeGen_call_UpdateFunction(self, instanceVarname, manifest, language):
        lines = 'if (' +  self.triggerSignal.name + ') {\n'
        lines += GenericSubsystem.codeGen_call_UpdateFunction(self, instanceVarname, manifest, language)
        lines += '}\n'

        return lines
        
def triggered_subsystem( manifest, inputSignals : List[SignalUserTemplate], trigger : SignalUserTemplate ):
    return wrap_signal_list( TruggeredSubsystem( get_simulation_context(), manifest, unwrap_hash( inputSignals ), unwrap( trigger ) ).outputSignals )

        





class ForLoopSubsystem(GenericSubsystem):
    """
        Include a triggered sub-system by passing a manifest
    """
    def __init__(self, sim : Simulation, manifest, inputSignals, i_max : Signal ):

        # TODO: add this signal to the blocks inputs
        self.i_max_signal = i_max

        GenericSubsystem.__init__(self, sim=sim, manifest=manifest, inputSignals=inputSignals, additionalInputs=[ i_max ] )

    def returnDependingInputs(self, outputSignal):

        # NOTE: This is a simplified veriant so far.. no dependence on the given 'outputSignal'
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

    def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            # return self.outputSignal(0).getName() + ' = ' + str( self.constant ) + ';\n'
            return signal.name + ' = ' + str( self.constant ) + ';\n'

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

    def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            # return self.outputSignal(0).getName() + ' = ' + str(self._factor) + ' * ' + self.inputSignal(0).getName() +  ';\n'
            return signal.name + ' = ' + str(self._factor) + ' * ' + self.inputSignal(0).name +  ';\n'

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

    def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            # TODO: only = is used and the c++ compiler decides how to convert...
            return signal.name + ' = ' + self.inputSignal(0).name + ';\n'

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

    def codeGen_output(self, language, signal : Signal):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(self.factors[i]) + ' * ' + s.getName() )
                i = i + 1

            sumline = ' + '.join( strs )
            lines = signal.name + ' = ' + sumline + ';\n'

            return lines

def dyn_add(sim : Simulation, inputSignals : List[SignalUserTemplate], factors : List[float]):
    return wrap_signal( Add(sim, unwrap_list( inputSignals ), factors).outputSignals )

def add(inputSignals : List[SignalUserTemplate], factors : List[float]):
    return wrap_signal( Add(get_simulation_context(), unwrap_list( inputSignals ), factors).outputSignals )


class Operator1(StaticFn_NTo1):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], operator : str ):

        self.operator = operator
        StaticFn_NTo1.__init__(self, sim, inputSignals)

    def codeGen_output(self, language, signal : Signal):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(  s.getName() ) )
                i = i + 1

            sumline = (' ' + self.operator + ' ').join( strs )
            lines = signal.name + ' = ' + sumline + ';\n'

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

    def codeGen_output(self, language, signal : Signal):

        if language == 'c++':
            lines = signal.name + ' = ' + self.inputSignals[0].name + ' ' + self.operator + ' ' + self.inputSignals[1].name + ';\n'
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

    def codeGen_output(self, language, signal : Signal):

        if language == 'c++':
            lines = '\n// switch ' + str(len(self.inputs)) + ' inputs --> ' + self.state.name + '\n'
            i = 1
            for ip in self.inputs:
                if i == 1:
                    lines += 'if (' + self.state.name + ' == ' + str(i) + ') {\n'
                else:
                    lines += 'else if (' + self.state.name + ' == ' + str(i) + ') {\n'

                lines += '  ' + signal.name + ' = ' + ip.name + ';\n'
                lines += '} '

                i += 1

            lines += 'else {\n'
            lines += '  ' + signal.name + ' = ' + self.inputs[0].name + ';\n'
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

    def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            return signal.name + ' = ' + str(self._functionName) + '(' + self.inputSignal(0).getName() +  ');\n'


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
    def __init__(self, sim : Simulation, u : Signal ):

        StaticFn_1To1.__init__(self, sim, u)

    def codeGen_defStates(self, language):
        if language == 'c++':
            return self.outputType.cppDataType + ' ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

    def codeGen_output(self, language, signal : Signal):
        if language == 'c++':
            return signal.name + ' = ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

    def codeGen_update(self, language):
        if language == 'c++':
            return self.getUniqueVarnamePrefix() + '_previousOutput' + ' = ' + self.inputSignal(0).getName() + ';\n'

    def codeGen_reset(self, language):
        if language == 'c++':
            return self.getUniqueVarnamePrefix() + '_previousOutput' + ' = 0;\n'


def dyn_delay(sim : Simulation, u : SignalUserTemplate ):
    return wrap_signal( Delay(sim, u.unwrap ).outputSignals )

def delay(u : SignalUserTemplate):
    return wrap_signal( Delay(get_simulation_context(), u.unwrap ).outputSignals )



