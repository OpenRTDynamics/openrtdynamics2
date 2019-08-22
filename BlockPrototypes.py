from libdyn import *
from Signal import *
from Block import *
from SimulationContext import *
from BlockInterface import *

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




class GenericSubsystem(BlockPrototype):
    """
        Include a sub-system by passing a manifest
    """
    def __init__(self, sim : Simulation, manifest, inputSignals, additionalInputs : List[ Signal ] = None ):
        # intputSignals is a hash array
        #
        # intputSignals = {'in1': in1, 'in2', : in2}

        self.manifest = manifest

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

                # check datatype (NOTE: MOVE.. not possible here in the contructor)
                if not signal.getDatatype().cppDataType == dependingInput_cpptype:
                    raise BaseException('datatype does not match the one specified in the manifest. (' + (dependingInput_cpptype) + ' is required in the manifest)' )

                # append signal
                dependingInputs.append( signal ) 

            return dependingInputs

        # collect all depending input signals (that are needed to calculate the output) in a list
        self.dependingInputs = collectDependingSignals( inputSignals, manifest.io_inputs['calculate_output'] )

        # collect all inputs required to perform the state update
        self.inputsToUpdateStates = collectDependingSignals( inputSignals, manifest.io_inputs['state_update'] )

        # combine all inputs to a list
        if additionalInputs is not None:
            self.allInputs = additionalInputs

        else:
            self.allInputs = {}

        self.allInputs.extend( self.dependingInputs )
        self.allInputs.extend( self.inputsToUpdateStates )

        # the number of outputs
        self.outputTypes = manifest.io_outputs['calculate_output']['types']  
        Noutputs = len( manifest.io_outputs['calculate_output']['names'] )

        BlockPrototype.__init__(self, sim, self.allInputs, Noutputs)

        # for code generation
        self.instanceVarname = self.getUniqueVarnamePrefix() + '_subsystem_' + self.manifest.API_name

    def configDefineOutputTypes(self, inputTypes):

        # the datatypes are fixed in the manifest 
        return self.outputTypes        

    def returnDependingInputs(self, outputSignal):

        # NOTE: This is a simplified veriant so far.. no dependence on the given 'outputSignal'
        #       (Every output depends on every signal in self.dependingInputs)

        return self.dependingInputs

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
        # TODO: must be called from the code generation framework
        self.codeGen_outputsCalculated = False

        self.isSignalVariableDefined = {}
        for s in self.outputSignals:
            self.isSignalVariableDefined[ s ] = False

    def codeGen_destruct(self, language):
        pass

    def codeGen_setOutputReference(self, language, signal):
        # infcates that for signal, no localvar will be reserved, but a reference to that data is used
        # This is the case for signals that are system outputs

        # 
        self.isSignalVariableDefined[ signal ] = True


    def codeGen_call_OutputFunction(self, instanceVarname, manifest, language):
        return instanceVarname + '.' + manifest.getAPIFunctionName('calculate_output') +  '(' + cgh.signalListHelper_names_string(self.outputSignals + self.dependingInputs) + ');\n'

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
                # input to this call are the signals in self.dependingInputs

                lines += self.codeGen_call_OutputFunction(self.instanceVarname, self.manifest, language)

                self.codeGen_outputsCalculated = True

            else:
                lines = ''

        return lines

    def codeGen_update(self, language):
        if language == 'c++':

            # input to this call are the signals in self.inputsToUpdateStates
            return self.codeGen_call_UpdateFunction(self.instanceVarname, self.manifest, language)

def generic_subsystem( manifest, inputSignals : List[Signal] ):
    return GenericSubsystem(get_simulation_context(), manifest, inputSignals).outputSignals





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
        #       (Every output depends on every signal in self.dependingInputs)

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
        
def triggered_subsystem( manifest, inputSignals : List[Signal], trigger : Signal ):
    return TruggeredSubsystem( get_simulation_context(), manifest, inputSignals, trigger ).outputSignals

        





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
        #       (Every output depends on every signal in self.dependingInputs)

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
        
def for_loop_subsystem( manifest, inputSignals : List[Signal], i_max : Signal ):
    return ForLoopSubsystem( get_simulation_context(), manifest, inputSignals, i_max ).outputSignals

        



            


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
    return Const(sim, constant, datatype).outputSignals

def const(constant, datatype ):
    return Const(get_simulation_context(), constant, datatype).outputSignals




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
    return Gain(sim, u, gain).outputSignals

def gain(u : Signal, gain : float ):
    return Gain(get_simulation_context(), u, gain).outputSignals



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

def dyn_add(sim : Simulation, inputSignals : List[Signal], factors : List[float]):
    return Add(sim, inputSignals, factors).outputSignals

def add(inputSignals : List[Signal], factors : List[float]):
    return Add(get_simulation_context(), inputSignals, factors).outputSignals


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


def dyn_operator1(sim : Simulation, inputSignals : List[Signal], operator : str ):
    return Operator1(sim, inputSignals, operator).outputSignals

def operator1(inputSignals : List[Signal], operator : str ):
    return Operator1(get_simulation_context(), inputSignals, operator).outputSignals






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


def comparison(left : Signal, right : Signal, operator : str ):
    return ComparisionOperator(get_simulation_context(), left, right, operator).outputSignals



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


def dyn_sin(sim : Simulation, u : Signal ):
    return StaticFnByName_1To1(sim, u, 'sin').outputSignals

def dyn_cos(sim : Simulation, u : Signal ):
    return StaticFnByName_1To1(sim, u, 'cos').outputSignals

def sin(u : Signal ):
    return StaticFnByName_1To1(get_simulation_context(), u, 'sin').outputSignals

def cos(u : Signal ):
    return StaticFnByName_1To1(get_simulation_context(), u, 'cos').outputSignals



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


def dyn_delay(sim : Simulation, inputSignals : Signal ):
    return Delay(sim, inputSignals).outputSignals

def delay(inputSignals : Signal):
    return Delay(get_simulation_context(), inputSignals).outputSignals



