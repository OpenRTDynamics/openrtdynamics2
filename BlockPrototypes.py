from libdyn import *
from Signal import *
from Block import *
from irpar import *

#
# block definitions
#



class Padd(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], factors : List[float] ):

        # 
        self.inputSignals = inputSignals

        # TODO: allow a list of inputs  TODO: Do this next!
        if len(inputSignals) != len(factors):
            raise("len(inp_list) must be equal to len(factors)")

        self.factors = factors

        blk = Block(sim, self, inputSignals, blockname = 'add').configAddOutputSignal('sum')


        # call super
        BlockPrototype.__init__(self, blk)

        # optional to initially fix the output types:
        # self.outputSignal(0).setDatatype(  ...  )


    def configDefineOutputTypes(self, inputTypes):
        # print("Padd: in callback configDefineOutputTypes")


        if self.outputSignal(0).getDatatype() is None:
            #
            # no output type defined so far..
            # look for an already defined input type and inherit.
            #

            print(self.block.toStr() )

            for t in inputTypes:
                if t is not None:
                    print(" - (intype) " + t.toStr() ) 
                else:
                    print(" - (NONE)") 


            # set a proposal for an output type. Choose the best numeric precission
            # for the output according to the already defined input types.
            # 
            self.outputType = computeResultingNumericType(inputTypes)

            print('Padd (' + self.block.toStr() + '): proposed outputtype of ' + self.outputSignal(0).getName() + ' is: ' + self.outputType.toStr() + '')

        else:

            # check of the given output type is a numeric datatype
            if not isinstance( self.outputSignal(0).getDatatype(), DataTypeNumeric ):
                raise BaseException("Padd: only DataTypeNumeric can be the result/output of an addition")
        
        return [self.outputType]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output (there is only one) depends on all inputs
        return self.inputSignals 

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return []

    def getOutputsSingnals(self):
        # return the output signals
        sum = self.outputSignal(0)

        return sum

    def encode_irpar(self):
        ipar = []
        rpar = self.factors

        return ipar, rpar

    def getORTD_btype(self):
        # The ORTD interpreter finds the computational function using this id
        return 12

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'defStates':
                lines = ''

            elif flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':

                strs = []
                i = 0
                for s in self.inputSignals:
                    strs.append(  str(self.factors[i]) + ' * ' + s.getName() )
                    i = i + 1

                sumline = ' + '.join( strs )

                lines = self.outputSignal(0).getName() + ' = ' + sumline + ';\n'

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = '// nothing to reset for ' + self.block.getName() + '\n'

        return lines




def dyn_add(sim : Simulation, inputSignals : List[Signal], factors : List[float]):

    return Padd(sim, inputSignals, factors).getOutputsSingnals()







class Pconst(BlockPrototype):
    def __init__(self, sim : Simulation, constant, datatype ):

        self.constant = constant
        self.outputType = datatype

        #
        blk = Block(sim, self, None, blockname = 'const').configAddOutputSignal('const')

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

    def getOutputsSingnals(self):
        # return the output signals
        const = self.outputSignal(0)

        return const

    def encode_irpar(self):
        ipar = []
        rpar = self.constant

        return ipar, rpar

    def getORTD_btype(self):
        # The ORTD interpreter finds the computational function using this id
        return 40

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'defStates':
                lines = ''

            elif flag == 'localvar':
                lines = self.outputType.cppDataType + ' const ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = self.outputSignal(0).getName() + ' = ' + str( self.constant ) + ';\n'

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''

        return lines



def dyn_const(sim : Simulation, constant, datatype ):

    return Pconst(sim, constant, datatype).getOutputsSingnals()











class Pdelay(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal ):

        self.u = u
        self.outputType = None

        #
        blk = Block(sim, self, [ u ], blockname = 'delay').configAddOutputSignal('z^-1 input') # TODO: inherit the name of the input (nice to have)

        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):
        # print("Pdelay: in callback configDefineOutputTypes")

        # just inherit the input type 
        if inputTypes[0] is not None:
            self.outputType = inputTypes[0]
        else:
            self.outputType = None

        # self.outputSignal(0).setDatatype(  self.outputType  )

        return [ self.outputType ]
 

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # no (direct feedtrough) dependence on any input - only state dependent
        return [  ]

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return [self.u]  # all inputs

    def getOutputsSingnals(self):
        # return the output signals

        return self.outputSignal(0)

    def encode_irpar(self):
        ipar = []
        rpar = self.factors

        return ipar, rpar

    def getORTD_btype(self):
        # The ORTD interpreter finds the computational function using this id
        return 12

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'defStates':
                lines = self.outputType.cppDataType + ' ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

            elif flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = self.outputSignal(0).getName() + ' = ' + self.getUniqueVarnamePrefix() + '_previousOutput' + ';\n'

            elif flag == 'update':
                lines = self.getUniqueVarnamePrefix() + '_previousOutput' + ' = ' + self.inputSignal(0).getName() + ';\n'

            elif flag == 'reset':
                lines = self.getUniqueVarnamePrefix() + '_previousOutput' + ' = 0;\n'

        return lines


def dyn_delay(sim : Simulation, inputSignals : Signal ):

    return Pdelay(sim, inputSignals).getOutputsSingnals()








class Pgain(BlockPrototype):
    def __init__(self, sim : Simulation, u : Signal, gain : float ):

        self.u = u
        self.gain = gain
        self.outputType = None

        #
        blk = Block(sim, self, [ u ], blockname = 'gain').configAddOutputSignal('gain')
        
        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):
        # print("Pdelay: in callback configDefineOutputTypes")

        # just inherit the input type 
        if inputTypes[0] is not None:
            self.outputType = inputTypes[0]
        else:
            self.outputType = None

        # self.outputSignal(0).setDatatype(  self.outputType  )

        return [ self.outputType ]        

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on the only one input signals
        return [ self.u ]

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return []  # no inputs

    def getOutputsSingnals(self):
        # return the output signals

        return self.outputSignal(0)

    def encode_irpar(self):
        ipar = []
        rpar = self.factors

        return ipar, rpar

    def getORTD_btype(self):
        # The ORTD interpreter finds the computational function using this id
        return -1

    def codeGen(self, language, flag):

        lines = ''

        if language == 'c++':

            if flag == 'defStates':
                lines = ''
                
            elif flag == 'localvar':
                lines = self.outputType.cppDataType + ' ' + self.outputSignal(0).getName() + ';\n'

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = self.outputSignal(0).getName() + ' = ' + str(self.gain) + ' * ' + self.inputSignal(0).getName() +  ';\n'

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''

        return lines


def dyn_gain(sim : Simulation, u : Signal, gain : float ):

    return Pgain(sim, u, gain).getOutputsSingnals()


