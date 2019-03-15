

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


    def configDefineOutputTypes(self):
        print("Padd: in callback configDefineOutputTypes")


        # check if inputs are double
        RequestedType = DataType( ORTD_DATATYPE_FLOAT, 1 )

        # if not InTypes.getType(0).isEqualTo( RequestedType ):
        #     print("wrong datatype in add function at input port 0")

        # if not InTypes.getType(1).isEqualTo( RequestedType ):
        #     print("wrong datatype in add function at input port 1")

        # just copy the input type from inport 0
        inputType = self.blk.getInputSignal(0).getDatatype()
        outSignal = self.blk.GetOutputSignal(0).setDatatype(  inputType  )





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

        self.blk.GetOutputSignal(0).setDatatype(  DataType( ORTD_DATATYPE_FLOAT, 1 )  )


        # call super
        #BlockPrototype.__init__(self)

    def configDefineOutputTypes(self):

        print("Pconst: in callback configDefineOutputTypes")


        pass

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











class Pdelay(BlockPrototype):
    def __init__(self, sim : Simulation, inputSignals : Signal ):

        self.inputSignals = inputSignals

        # outputs. This is a definition of the output ports and the data types known so far
        # TODO: remove these and use the output signals
        OutputDef = OutputDefinitions(  [  DataType( None, None ) ]  )  # None means type and size are not known so far

        #
        self.blk = Block(sim, self, [ inputSignals ], OutputDef, blockname = 'delay')
        sim.addBlock(self.blk)


    #def defineOutputTypes(self):
        # TODO: 15.3.19
        # Check input signal types and update output signal types accordingly




    def configDefineOutputTypes(self):
        # TODO: 15.3.19
        # Check input signal types and update output signal types accordingly

        print("Pdelay: in callback configDefineOutputTypes")

        # just copy the input type 
        inputType = self.blk.getInputSignal(0).getDatatype()
        outSignal = self.blk.GetOutputSignal(0).setDatatype(  inputType  )



        # check if inputs are double
        # RequestedType = DataType( ORTD_DATATYPE_FLOAT, 1 )

    #     if not InTypes.getType(0).isEqualTo( RequestedType ):
    #         print("wrong datatype in add function at input port 0")

    #     # TODO: set the output type!


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


def dyn_delay(sim : Simulation, inputSignals : Signal ):

    return Pdelay(sim, inputSignals).GetOutputsSingnals()




