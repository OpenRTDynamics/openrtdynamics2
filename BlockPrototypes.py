from libdyn import *
from Signal import *
from Block import *
from SimulationContext import *
from BlockInterface import *

import CodeGenHelper as cgh

#
# block templates for common use-cases
#

class Source_To1(BlockPrototype):
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
        return []

    @property
    def outputSignals(self):
        # return the output signals
        output = self.outputSignal(0)

        return output




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
        return []  # no inputs

    @property
    def outputSignals(self):
        # return the output signals

        return self.outputSignal(0)

    def codeGen_localvar(self, language):
        if language == 'c++':
            return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'




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
        return []

    @property
    def outputSignals(self):
        # return the output signals
        output = self.outputSignal(0)

        return output

    def codeGen_localvar(self, language):
        if language == 'c++':
            return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'



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

    def codeGen_localvar(self, language):
        if language == 'c++':
            return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'




#
# To include a sub-system by passing a manifest
#
# manifest['api_name']
#

# STOPPED HERE


class GenericSubsystem(BlockPrototype):
    def __init__(self, sim : Simulation, manifest, inputSignals ):
        # intputSignals is a hash array
        #
        # intputSignals = {'in1': in1, 'in2', : in2}

        # self.inputSignals = inputSignals
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
        self.allInputs = []
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

    @property
    def outputSignals(self):
        # return the output signals

        return self._outputSignals

    def codeGen_defStates(self, language):
        if language == 'c++':
            lines = '// instance of ' + self.manifest.API_name + '\n'
            lines += self.manifest.API_name + ' ' + self.instanceVarname + ';\n'

            return lines

    def codeGen_reset(self, language):
        if language == 'c++':
            return self.instanceVarname + '.' + self.manifest.getAPIFunctionName('reset') +  '();\n'


    def codeGen_localvar(self, language):
        # TODO: every block prototype shall befine its variables like this.. move this to BlockPrototype and remove all individual implementations
        if language == 'c++':
            return cgh.defineVariables( self.outputSignals )

    def codeGen_output(self, language):
        if language == 'c++':
            
            # input to this call are the signals in self.dependingInputs
            return self.instanceVarname + '.' + self.manifest.getAPIFunctionName('calculate_output') +  '(' + cgh.signalListHelper_names_string(self.outputSignals + self.dependingInputs) + ');\n'

    def codeGen_update(self, language):
        if language == 'c++':

            # input to this call are the signals in self.inputsToUpdateStates
            return self.instanceVarname + '.' + self.manifest.getAPIFunctionName('state_update') +  '(' + cgh.signalListHelper_names_string(self.inputsToUpdateStates) + ');\n'



    # def codeGen_defStates(self, language):
    #     if language == 'c++':
    #         return self.outputType.cppDataType + ' ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

    # def codeGen_output(self, language):
    #     if language == 'c++':
    #         return self.outputSignal(0).getName() + ' = ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

    # def codeGen_update(self, language):
    #     if language == 'c++':
    #         return self.getUniqueVarnamePrefix() + '_previousOutput' + ' = ' + self.inputSignal(0).getName() + ';\n'

    # def codeGen_reset(self, language):
    #     if language == 'c++':
    #         return self.getUniqueVarnamePrefix() + '_previousOutput' + ' = 0;\n'



def generic_subsystem( manifest, inputSignals : List[Signal] ):
    return GenericSubsystem(get_simulation_context(), manifest, inputSignals).outputSignals






#
# Sources
#

class Const(Source_To1):
    def __init__(self, sim : Simulation, constant, datatype ):

        self.constant = constant

        # call super
        Source_To1.__init__(self, sim, datatype)

    def codeGen_localvar(self, language):
        if language == 'c++':
            return self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

    def codeGen_output(self, language):
        if language == 'c++':
            return self.outputSignal(0).getName() + ' = ' + str( self.constant ) + ';\n'

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

    def codeGen_output(self, language):
        if language == 'c++':
            return self.outputSignal(0).getName() + ' = ' + str(self._factor) + ' * ' + self.inputSignal(0).getName() +  ';\n'

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

    def codeGen_output(self, language):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(self.factors[i]) + ' * ' + s.getName() )
                i = i + 1

            sumline = ' + '.join( strs )
            lines = self.outputSignal(0).getName() + ' = ' + sumline + ';\n'

            return lines

def dyn_add(sim : Simulation, inputSignals : List[Signal], factors : List[float]):
    return Add(sim, inputSignals, factors).outputSignals

def add(inputSignals : List[Signal], factors : List[float]):
    return Add(get_simulation_context(), inputSignals, factors).outputSignals


class Operator1(StaticFn_NTo1):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], operator : str ):

        self.operator = operator
        StaticFn_NTo1.__init__(self, sim, inputSignals)

    def codeGen_output(self, language):

        if language == 'c++':
            strs = []
            i = 0
            for s in self.inputSignals:
                strs.append(  str(  s.getName() ) )
                i = i + 1

            sumline = (' ' + self.operator + ' ').join( strs )
            lines = self.outputSignal(0).getName() + ' = ' + sumline + ';\n'

            return lines


def dyn_operator1(sim : Simulation, inputSignals : List[Signal], operator : str ):
    return Operator1(sim, inputSignals, operator).outputSignals

def operator1(inputSignals : List[Signal], operator : str ):
    return Operator1(get_simulation_context(), inputSignals, operator).outputSignals



#
# Static functions that map 1 --> 1
#

class StaticFnByName_1To1(StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, functionName : str ):

        self._functionName = functionName

        StaticFn_1To1.__init__(self, sim, u)

    def codeGen_output(self, language):
        if language == 'c++':
            return self.outputSignal(0).getName() + ' = ' + str(self._functionName) + '(' + self.inputSignal(0).getName() +  ');\n'


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

    def codeGen_output(self, language):
        if language == 'c++':
            return self.outputSignal(0).getName() + ' = ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

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



