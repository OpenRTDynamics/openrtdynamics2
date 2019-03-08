from typing import Dict, List


ORTD_DATATYPE_UNCONFIGURED = 0
ORTD_DATATYPE_FLOAT = (1 | (8 << 5))
ORTD_DATATYPE_SHORTFLOAT = 4
ORTD_DATATYPE_INT32 = 2
ORTD_DATATYPE_BOOLEAN = 3
ORTD_DATATYPE_EVENT = 5
ORTD_DATATYPE_BINARY = 6
ORTD_DATATYPE_UINT32 = 7
ORTD_DATATYPE_INT16 = 8
ORTD_DATATYPE_UINT16 = 9
ORTD_DATATYPE_INT8 = 10
ORTD_DATATYPE_UINT8 = 11


class Signal:
    def __init__(self, sim, datatype = None, sourceBlock = None, sourcePort = None):
        self.sim = sim
        self.datatype = datatype
        self.sourceBlock = sourceBlock
        self.sourcePort = sourcePort  # counting starts at zero

        # the list of destinations this signals goes to
        self.destinationBlocks = []
        self.destinationPorts = []

        #if sourceBlock == None:
            # create a signal without any specified origin

    def addDestination(self, block , port : int):
        # add this destination to the list
        self.destinationBlocks.append( block )
        self.destinationPorts.append( port )


    def setequal(self, From ):
        #if self.sim != From.sim:
        #    throw("setequal: From signal must be from the same simulation")

        # TODO Handle destinations here

        if self.datatype == None:
            self.datatype = From.datatype
        elif not self.datatype.isEqualTo( From.datatype ):
            raise("setqual: datatype missmatch")
        else:
            self.datatype = From.datatype

        self.sourceBlock = From.sourceBlock
        self.sourcePort = From.sourcePort

    def getDatatype(self):
        return self.datatype

    def ShowOrigin(self):
        if not self.sourcePort is None and not self.sourceBlock is None:
            print("Signal origin: port " + str(self.sourcePort) + " of block #" + str(self.sourceBlock.getId()) )

        else:
            print("Signal origin not defined (so far)")

