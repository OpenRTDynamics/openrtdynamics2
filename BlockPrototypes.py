

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

        #
        if len(inputSignals) != 2:
            raise("inp_list must have exactly 2 elements")


        self.fak_list = fak_list

        blk = Block(sim, self, inputSignals, blockname = 'add').configAddOutputSignal('sum')

        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):
        # print("Padd: in callback configDefineOutputTypes")

        # check if inputs are double
        requestedType = DataType( ORTD_DATATYPE_FLOAT, 1 )

        if inputTypes[0] is not None:
            if inputTypes[0].isEqualTo( inputTypes[1] ) == 0:
                raise BaseException("input types do not match (must be equal to perform addition): " + inputTypes[0].toStr() + " != " + inputTypes[1].toStr() )

        if not requestedType.isEqualTo( inputTypes[0] ):
            raise BaseException("input type not float")

        if not requestedType.isEqualTo( inputTypes[1] ):
            raise BaseException("input type not float")

        # return [ inputTypes[0] ]
        return [requestedType]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output (there is only one) depends on all inputs
        return self.inputSignals 

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return []

    def GetOutputsSingnals(self):
        # return the output signals
        #sum = self.blk.GetOutputSignal(0)

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

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = 'double ' + self.outputSignal(0).getName() 
                + ' = ' + self.inputSignal(0).getName() + ' + ' 
                + self.inputSignal(1).getName()

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''

        return lines




def dyn_add(sim : Simulation, inputSignals : List[Signal], fak_list : List[float]):

    return Padd(sim, inputSignals, fak_list).GetOutputsSingnals()







class Pconst(BlockPrototype):
    def __init__(self, sim : Simulation, constant : float ):

        self.constant = constant

        #
        blk = Block(sim, self, None, blockname = 'const').configAddOutputSignal('const')

        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):
        # print("Pconst: in callback configDefineOutputTypes")

        # define the output type 
        return [ DataType( ORTD_DATATYPE_FLOAT, 1 ) ]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on nothing
        return []

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return []

    def GetOutputsSingnals(self):
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

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = ''

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''



def dyn_const(sim : Simulation, constant : float ):

    return Pconst(sim, constant).GetOutputsSingnals()











class Pdelay(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignal : Signal ):

        self.inputSignal = inputSignal

        #
        blk = Block(sim, self, [ inputSignal ], blockname = 'delay').configAddOutputSignal('z^-1 input') # TODO: inherit the name of the input (nice to have)

        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):
        # print("Pdelay: in callback configDefineOutputTypes")

        # just copy the input type 
        return [ inputTypes[0] ]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on the only one input signals
        # return [ self.inputSignal ]

        # no (direct feedtrough) dependence on any input - only state dependent
        return [  ]

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return [self.inputSignal]  # all inputs

    def GetOutputsSingnals(self):
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
                lines = ''

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = ''

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''


def dyn_delay(sim : Simulation, inputSignals : Signal ):

    return Pdelay(sim, inputSignals).GetOutputsSingnals()








class Pgain(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignal : Signal, gain : float ):

        self.inputSignal = inputSignal

        #
        blk = Block(sim, self, [ inputSignal ], blockname = 'gain').configAddOutputSignal('gain')
        
        # call super
        BlockPrototype.__init__(self, blk)


    def configDefineOutputTypes(self, inputTypes):
        # print("Pdelay: in callback configDefineOutputTypes")

        # just copy the input type 
        return [ inputTypes[0] ]

    def returnDependingInputs(self, outputSignal):
        # return a list of input signals on which the given output signal depends on

        # the output depends on the only one input signals
        return [ self.inputSignal ]

    def returnInutsToUpdateStates(self, outputSignal):
        # return a list of input signals that are required to update the states
        return []  # no inputs

    def GetOutputsSingnals(self):
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

            elif flag == 'constructor':
                lines = ''

            elif flag == 'destructor':
                lines = ''

            elif flag == 'output':
                lines = ''

            elif flag == 'update':
                lines = ''

            elif flag == 'reset':
                lines = ''



def dyn_gain(sim : Simulation, inputSignal : Signal, gain : float ):

    return Pgain(sim, inputSignal, gain).GetOutputsSingnals()


