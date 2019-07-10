from libdyn import *
from Signal import *
from Block import *
from irpar import *

#
# block definitions
#






class StaticFn_1To1(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal ):

        self.u = u
        self.outputType = None

        # create a new block
        blk = Block(sim, self, [ u ], blockname = '').configAddOutputSignal()
        
        # call super-class constructor
        BlockPrototype.__init__(self, blk)


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




class Gain(StaticFn_1To1):
    def __init__(self, sim : Simulation, u : Signal, factor : float ):

        self._factor = factor

        StaticFn_1To1.__init__(self, sim, u)

    def codeGen_output(self, language):
        if language == 'c++':
            return self.outputSignal(0).getName() + ' = ' + str(self._factor) + ' * ' + self.inputSignal(0).getName() +  ';\n'

def dyn_gain(sim : Simulation, u : Signal, gain : float ):

    return Gain(sim, u, gain).outputSignals





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










class Padd(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], factors : List[float] ):

        # 
        self.inputSignals = inputSignals

        # feasibility checks
        if len(inputSignals) != len(factors):
            raise("len(inp_list) must be equal to len(factors)")

        self.factors = factors

        blk = Block(sim, self, inputSignals, blockname = 'add').configAddOutputSignal()

        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):

        # check if the output signal type is already defined (e.g. by the user)
        if self.outputSignal(0).getDatatype() is None:
            #
            # no output type defined so far..
            # look for an already defined input type and inherit that type.
            #

            self.outputType = computeResultingNumericType(inputTypes)

            print('Padd (' + self.block.toStr() + '): proposed outputtype of ' + self.outputSignal(0).getName() + ' is: ' + self.outputType.toStr() + '')

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
    def outputSingnals(self):
        # return the output signals
        output = self.outputSignal(0)

        return output

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'output':

                strs = []
                i = 0
                for s in self.inputSignals:
                    strs.append(  str(self.factors[i]) + ' * ' + s.getName() )
                    i = i + 1

                sumline = ' + '.join( strs )

                lines = self.outputSignal(0).getName() + ' = ' + sumline + ';\n'


        return lines




def dyn_add(sim : Simulation, inputSignals : List[Signal], factors : List[float]):

    return Padd(sim, inputSignals, factors).outputSingnals





class Poperator1(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], operator ):

        # 
        self.inputSignals = inputSignals

        self.operator = operator

        blk = Block(sim, self, inputSignals, blockname = 'operator1').configAddOutputSignal()


        # call super
        BlockPrototype.__init__(self, blk)

        # optional to initially fix the output types:
        # self.outputSignal(0).setDatatype(  ...  )


    def configDefineOutputTypes(self, inputTypes):
        # print("Padd: in callback configDefineOutputTypes")


        if self.outputSignal(0).getDatatype() is None:
            #
            # no output type defined so far..
            # look for an already defined input type and inherit that type.
            #

            self.outputType = computeResultingNumericType(inputTypes)

            print('Padd (' + self.block.toStr() + '): proposed outputtype of ' + self.outputSignal(0).getName() + ' is: ' + self.outputType.toStr() + '')

        else:

            # check of the given output type is a numeric datatype
            if not isinstance( self.outputSignal(0).getDatatype(), DataTypeNumeric ):
                raise BaseException("Poperator1: only DataTypeNumeric can be the result/output of an addition")
        
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

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'output':

                strs = []
                i = 0
                for s in self.inputSignals:
                    strs.append(  str(  s.getName() ) )
                    i = i + 1

                sumline = (' ' + self.operator + ' ').join( strs )

                lines = self.outputSignal(0).getName() + ' = ' + sumline + ';\n'

        return lines




def dyn_operator1(sim : Simulation, inputSignals : List[Signal], operator ):

    return Poperator1(sim, inputSignals, operator).outputSignals






class Pconst(BlockPrototype):
    def __init__(self, sim : Simulation, constant, datatype ):

        self.constant = constant
        self.outputType = datatype

        #
        blk = Block(sim, self, None, blockname = 'const').configAddOutputSignal()

        # call super
        BlockPrototype.__init__(self, blk)

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

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'output':
                lines = self.outputSignal(0).getName() + ' = ' + str( self.constant ) + ';\n'

        return lines



def dyn_const(sim : Simulation, constant, datatype ):

    return Pconst(sim, constant, datatype).outputSignals











class Pdelay(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal ):

        self.u = u
        self.outputType = None

        #
        blk = Block(sim, self, [ u ], blockname = 'delay').configAddOutputSignal()

        # call super
        BlockPrototype.__init__(self, blk)

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

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'defStates':
                lines = self.outputType.cppDataType + ' ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

            elif flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'output':
                lines = self.outputSignal(0).getName() + ' = ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

            elif flag == 'update':
                lines = self.getUniqueVarnamePrefix() + '_previousOutput' + ' = ' + self.inputSignal(0).getName() + ';\n'

            elif flag == 'reset':
                lines = self.getUniqueVarnamePrefix() + '_previousOutput' + ' = 0;\n'

        return lines


def dyn_delay(sim : Simulation, inputSignals : Signal ):

    return Pdelay(sim, inputSignals).outputSignals







# # becomes obsolete
# class Pgain(BlockPrototype):
#     def __init__(self, sim : Simulation, u : Signal, gain : float ):

#         self.u = u
#         self.gain = gain
#         self.outputType = None

#         # create a new block
#         blk = Block(sim, self, [ u ], blockname = 'gain').configAddOutputSignal()
        
#         # call super-class constructor
#         BlockPrototype.__init__(self, blk)


#     def configDefineOutputTypes(self, inputTypes):

#         # just inherit the input type 
#         if inputTypes[0] is not None:
#             self.outputType = inputTypes[0]
#         else:
#             self.outputType = None

#         return [ self.outputType ]        

#     def returnDependingInputs(self, outputSignal):
#         # return a list of input signals on which the given output signal depends on

#         # the output depends on the only one input signals
#         return [ self.u ]

#     def returnInutsToUpdateStates(self, outputSignal):
#         # return a list of input signals that are required to update the states
#         return []  # no inputs

#     @property
#     def outputSignals(self):
#         # return the output signals

#         return self.outputSignal(0)

#     def codeGen(self, language, flag):

#         lines = ''

#         if language == 'c++':
                
#             if flag == 'localvar':
#                 lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

#             elif flag == 'output':
#                 lines = self.outputSignal(0).getName() + ' = ' + str(self.gain) + ' * ' + self.inputSignal(0).getName() +  ';\n'

#         return lines


# def dyn_gain(sim : Simulation, u : Signal, gain : float ):

#     return Pgain(sim, u, gain).outputSignals


