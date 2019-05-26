from libdyn import *
from Signal import *
from Block import *
from irpar import *

#
# block definitions
#



class Padd(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : List[Signal], fak_list : List[float] ):

        # 
        self.inputSignals = inputSignals

        # output type undefined
        #self.outputType = None
        #self.outputType = DataTypeFloat(1)

        # TODO: allow a list of inputs
        if len(inputSignals) != 2:
            raise("inp_list must have exactly 2 elements")

        self.fak_list = fak_list

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
            #self.outputSignal(0).setProposedDatatype( self.outputType )

            print('Padd (' + self.block.toStr() + '): proposed outputtype of ' + self.outputSignal(0).getName() + ' is: ' + self.outputType.toStr() + '')


            #if areAllTypesDefined(inputTypes):

            #    self.outputSignal(0).setDatatype( outputType )

            #else:

        else:

            # check of the given output type is a numeric datatype
            if not isinstance( self.outputSignal(0).getDatatype(), DataTypeNumeric ):
                raise BaseException("Padd: only DataTypeNumeric can be the result/output of an addition")

            # check if inputs are valid

            pass



            # if inputTypes[0] is not None:
            #     self.outputType = inputTypes[0]

            # else:
            #     if inputTypes[1] is not None:
            #         self.outputType = inputTypes[1]

        # else:
        #     #
        #     # an out type was defined
        #     # check that the inputs have the same type as the output
        #     #

        #     # TODO: allow int32 and double to be summed up. return the higher precission type

        #     if inputTypes[0] is not None:
        #         if inputTypes[0].isEqualTo( self.outputType ) == 0:
        #             raise BaseException("input types do not match (must be equal to perform addition): " + inputTypes[0].toStr() + " != " + self.outputType.toStr() )

            
        #     if inputTypes[1] is not None:
        #         if inputTypes[1].isEqualTo( self.outputType ) == 0:
        #             raise BaseException("input types do not match (must be equal to perform addition): " + inputTypes[1].toStr() + " != " + self.outputType.toStr() )

        
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
        rpar = self.fak_list

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
                lines = self.outputSignal(0).getName() + ' = ' + self.inputSignal(0).getName() + ' + ' + self.inputSignal(1).getName() + ';\n'

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = '// nothing to reset for ' + self.block.getName() + '\n'

        return lines




def dyn_add(sim : Simulation, inputSignals : List[Signal], fak_list : List[float]):

    return Padd(sim, inputSignals, fak_list).getOutputsSingnals()







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

    def getOperator(self):
        # don't know if this shall be kept
        return "const"

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

        # the output depends on the only one input signals
        # return [ self.u ]

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
        rpar = self.fak_list

        return ipar, rpar

    def getORTD_btype(self):
        # The ORTD interpreter finds the computational function using this id
        return 12

    def getOperator(self):
        # don't know if this shall be kept
        return "add"

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
        rpar = self.fak_list

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


