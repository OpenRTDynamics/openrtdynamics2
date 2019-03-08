

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
        if len(inputSignals) != 2:
            raise("inp_list must have exactly 2 elements")


        self.fak_list = fak_list

        # outputs. This is a definition of the output ports and the data types known so far
        OutputDef = OutputDefinitions(  [  DataType( None, None ) ]  )  # None means type and size are not known so far

        #
        self.blk = Block(sim, self, inputSignals, OutputDef, blockname = 'add')
        sim.addBlock(self.blk)

        # call super
        #BlockPrototype.__init__(self)

    def setPropagatedInputTypes(self, InTypes : InputDefinitions ):
        # check if inputs are double
        RequestedType = DataType( ORTD_DATATYPE_FLOAT, 1 )

        if not InTypes.getType(0).isEqualTo( RequestedType ):
            print("wrong datatype in add function at input port 0")

        if not InTypes.getType(1).isEqualTo( RequestedType ):
            print("wrong datatype in add function at input port 1")


        # TODO: set the output type!


        

    # def getOutputTypes(self):
    #     # shall return OutTypes : OutputDefinitions

    #     return OutputDefinitions(  [  DataType( ORTD_DATATYPE_FLOAT, 1 ) ]  )



    def GetOutputsSingnals(self):
        # return the output signals
        sum = self.blk.GetOutputSignal(0)

        return sum

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






def dyn_add(sim : Simulation, inputSignals : List[Signal], fak_list : List[float]):

    return Padd(sim, inputSignals, fak_list).GetOutputsSingnals()



class Pconst(BlockPrototype):
    def __init__(self, sim : Simulation, constant : float ):

        self.constant = constant

        # outputs. This is a definition of the output ports and the data types known so far


        # NEXT STEP 22.2.2019: check why these output definition are not considerd

        OutputDef = OutputDefinitions(  [  DataType( ORTD_DATATYPE_FLOAT, 1 ) ]  ) 
        
        #
        self.blk = Block(sim, self, None, OutputDef, blockname = 'const')
        sim.addBlock(self.blk)

        # call super
        #BlockPrototype.__init__(self)

    def setPropagatedInputTypes(self, InTypes : InputDefinitions ):
        # no inputs

        pass 

    # def getOutputTypes(self):
    #     # shall return OutTypes : OutputDefinitions

    #     return OutputDefinitions(  [  DataType( ORTD_DATATYPE_FLOAT, 1 ) ]  )



    def GetOutputsSingnals(self):
        # return the output signals
        sum = self.blk.GetOutputSignal(0)

        return sum

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



def dyn_const(sim : Simulation, constant : float ):

    return Pconst(sim, constant).GetOutputsSingnals()






